"""Recover exact historical image URLs from their linked first-party CDNs.

These responses are explicitly tagged as linked-origin material; they are not
misreported as Wayback captures. The allowlist is intentionally narrow.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import time
from urllib.parse import urljoin, urlsplit

import requests

from .archive import validate_payload
from .recover import suffix
from .state import State

ALLOWED_ORIGIN_HOSTS = {
    "static.squarespace.com", "static1.squarespace.com",
    "images.squarespace-cdn.com", "assets.squarespace.com",
}


class LinkedOriginClient:
    """Small, bounded HTTPS client restricted to observed Squarespace image URLs."""

    def __init__(self, session=None, delay: float = 0.5, timeout: int = 25,
                 max_bytes: int = 15_000_000, sleep=time.sleep):
        self.session = session or requests.Session()
        self.session.headers.update({
            "User-Agent": "BlueScholarsRestoration/0.1 (linked historical image; paced request)"
        })
        self.delay = max(0.0, float(delay))
        self.timeout = timeout
        self.max_bytes = max_bytes
        self.sleep = sleep

    @staticmethod
    def transport_url(url: str) -> str:
        parts = urlsplit(url)
        if (parts.scheme not in ("http", "https") or parts.hostname not in ALLOWED_ORIGIN_HOSTS
                or parts.username or parts.password):
            raise ValueError("Refusing linked-origin request outside the Squarespace image CDN allowlist")
        return parts._replace(scheme="https").geturl()

    def get(self, url: str):
        for _ in range(6):
            url = self.transport_url(url)
            self.sleep(self.delay)
            response = self.session.get(url, timeout=self.timeout, allow_redirects=False, stream=True)
            if response.status_code in (301, 302, 303, 307, 308):
                location = response.headers.get("Location", "")
                response.close()
                if not location:
                    raise ValueError("Linked-origin redirect has no Location")
                url = urljoin(url, location)
                continue
            if response.status_code != 200:
                status = response.status_code
                response.close()
                raise OSError(f"Linked-origin HTTP {status}")
            try:
                body = bytearray()
                for chunk in response.iter_content(chunk_size=65536):
                    body.extend(chunk)
                    if len(body) > self.max_bytes:
                        raise ValueError("Linked-origin image exceeds the size limit")
                return type("Payload", (), {
                    "body": bytes(body), "url": url, "status": response.status_code,
                    "headers": dict(response.headers),
                })()
            finally:
                response.close()
        raise ValueError("Too many linked-origin redirects")


def recover_linked_origin_images(state: State, client, max_files: int = 100) -> dict:
    """Save observed Squarespace image URLs still available from their CDN."""
    if max_files < 1:
        raise ValueError("max_files must be positive")
    eligible = []
    for record in state.data["resources"].values():
        parts = urlsplit(record.get("url", ""))
        # Squarespace shipped icon fonts as SVG files; discovery classifies by
        # suffix, but they are fonts, not raster/vector page images, and the
        # static renderer correctly refuses to publish SVG font glyphs.
        if "/universal/fonts/" in parts.path.lower():
            continue
        observed_referrers = [ref for ref in record.get("referrers", [])
                              if ref and not ref.startswith(("CDX:", "seed", "feed:"))]
        if (record.get("status") == "queued" and record.get("kind") == "image"
                and parts.scheme in ("http", "https") and parts.hostname in ALLOWED_ORIGIN_HOSTS
                and observed_referrers):
            eligible.append(record)
    eligible.sort(key=lambda row: ("bluescholars.com" not in " ".join(row.get("referrers", [])),
                                   row.get("url", "")))
    report = {"source_type": "linked_origin_asset", "attempted": 0, "recovered": 0,
              "failed": 0, "remaining_eligible": max(0, len(eligible) - max_files),
              "note": "Direct original CDN responses are not Wayback capture responses."}
    for record in eligible[:max_files]:
        url = record["url"]
        attempt = {"source_type": "linked_origin_asset", "source_url": url,
                   "at": datetime.now(timezone.utc).isoformat()}
        report["attempted"] += 1
        try:
            response = client.get(url)
            headers = {str(key).lower(): value for key, value in response.headers.items()}
            if response.status != 200:
                raise ValueError(f"Expected HTTP 200, received {response.status}")
            if not str(headers.get("content-type", "")).lower().startswith("image/"):
                raise ValueError("Linked-origin response did not declare an image content type")
            validate_payload(response.body, "image")
            digest = hashlib.sha256(response.body).hexdigest()
            raw_path = "recovery/raw/" + digest + suffix(response.body, "image")
            destination = state.root / raw_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            if not destination.exists():
                destination.write_bytes(response.body)
            record.update(status="recovered", raw_path=raw_path, sha256=digest,
                          bytes=len(response.body), source_type="linked_origin_asset",
                          source_url=url, final_url=response.url,
                          content_type=headers.get("content-type", ""),
                          retrieved_at=datetime.now(timezone.utc).isoformat(),
                          source_capture=None)
            attempt.update(result="downloaded", sha256=digest, bytes=len(response.body))
            report["recovered"] += 1
        except Exception as exc:
            attempt.update(result="failed", error=f"{type(exc).__name__}: {exc}")
            report["failed"] += 1
        record.setdefault("attempts", []).append(attempt)
        state.save()
    report["remaining_eligible"] = max(0, len(eligible) - report["attempted"])
    return report
