#!/usr/bin/env python3
"""Preserve publicly linked Blue Scholars event photos from their publisher.

This fallback is deliberately separate from Wayback mementos: source files are
fetched from the photographer's current site and gallery, then labeled as such.
The recovery remains local-only pending rights review.
"""
from __future__ import annotations

from restore.cooldown import ArchiveCooldown, RecoverySession
import hashlib
import json
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from restore.archive import validate_payload

ROOT = Path(__file__).resolve().parents[1]
PRESS = ROOT / "recovery/other-archives/press-articles"
OUT = ROOT / "recovery/other-archives/photographer-current"
RAW = OUT / "images"
MAX_BYTES = 25_000_000
ARTICLE_URL = "https://www.arminausejo.com/blue-scholars-kickstarter-vip-party/"


def collect() -> list[dict]:
    manifest = json.loads((PRESS / "manifest.json").read_text())
    refs = [row for row in manifest["page_captures"].values()
            if row.get("original_url") == ARTICLE_URL and (ROOT / row["raw_path"]).is_file()]
    if not refs:
        raise RuntimeError("No verified archived photographer article is available")
    refs.sort(key=lambda row: row["timestamp"], reverse=True)
    page = refs[0]
    soup = BeautifulSoup((ROOT / page["raw_path"]).read_bytes(), "html.parser")
    article = soup.select_one(".entry-content") or soup.select_one("article")
    if article is None:
        raise RuntimeError("Archived source page has no article body")
    found = {}
    for tag in article.find_all("img"):
        src = tag.get("src") or tag.get("data-src") or tag.get("data-original")
        alt = (tag.get("alt") or tag.get("title") or "").strip()
        if not src:
            continue
        url = urljoin(ARTICLE_URL, src)
        low = url.lower()
        if "blue-scholars" not in low and "blue-scholars-cinemetropolis" not in low:
            continue
        found[url] = {"url": url, "caption_or_alt": alt}
    if not found:
        raise RuntimeError("No explicitly Blue Scholars-labeled photo URLs found")
    return [{**value, "source_page": page} for value in found.values()]


def recover(delay: float = 1.0) -> dict:
    RAW.mkdir(parents=True, exist_ok=True)
    mpath = OUT / "manifest.json"
    existing = json.loads(mpath.read_text()) if mpath.exists() else {
        "source_type": "current publisher-hosted originals; not Wayback captures",
        "source_page_url": ARTICLE_URL,
        "captures": {},
    }
    session = RecoverySession()
    session.headers["User-Agent"] = "BlueScholarsHistoricalRecovery/0.1 (source-linked local preservation)"
    report = {"source_images": 0, "downloaded": 0, "reused": 0, "failures": [],
              "captured_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "publication_status": "local-only pending rights review"}
    for image in collect():
        report["source_images"] += 1
        url = image["url"]
        key = url
        old = existing["captures"].get(key)
        if old and (ROOT / old["raw_path"]).is_file():
            report["reused"] += 1
            continue
        try:
            response = session.get(url, timeout=(15, 60), stream=True)
            response.raise_for_status()
            body = bytearray()
            for chunk in response.iter_content(256 * 1024):
                if chunk:
                    body.extend(chunk)
                    if len(body) > MAX_BYTES:
                        raise ValueError("Image exceeds 25 MB cap")
            data = bytes(body)
            validate_payload(data, "image")
            content_type = response.headers.get("content-type", "")
            sha = hashlib.sha256(data).hexdigest()
            suffix = ".jpg" if data.startswith(b"\xff\xd8\xff") else ".png" if data.startswith(b"\x89PNG") else ".gif" if data.startswith((b"GIF87a", b"GIF89a")) else ".webp"
            path = RAW / f"{sha}{suffix}"
            if not path.exists():
                path.write_bytes(data)
            existing["captures"][key] = {
                "source_image_url": url,
                "final_url": response.url,
                "source_page_url": ARTICLE_URL,
                "source_page_capture_timestamp": image["source_page"]["timestamp"],
                "source_page_capture_sha256": image["source_page"]["sha256"],
                "source_article_published": "2011-06-17",
                "caption_or_alt": image["caption_or_alt"],
                "retrieved_at_utc": report["captured_at_utc"],
                "http_content_type": content_type,
                "bytes": len(data),
                "sha256": sha,
                "raw_path": path.relative_to(ROOT).as_posix(),
                "archive_status": "current publisher/gallery source; no exact Wayback image capture found",
                "rights_status": "unreviewed; local-only",
                "relevance_status": "source page explicitly identifies Blue Scholars or a named member",
            }
            report["downloaded"] += 1
        except ArchiveCooldown:
            raise
        except Exception as exc:
            report["failures"].append({"url": url, "error": f"{type(exc).__name__}: {exc}"})
        mpath.write_text(json.dumps(existing, indent=2, ensure_ascii=False) + "\n")
        time.sleep(delay)
    report["capture_records_total"] = len(existing["captures"])
    report["unique_payload_hashes_total"] = len({row["sha256"] for row in existing["captures"].values()})
    existing["last_report"] = report
    mpath.write_text(json.dumps(existing, indent=2, ensure_ascii=False) + "\n")
    (OUT / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    return report


if __name__ == "__main__":
    print(json.dumps(recover(), indent=2, ensure_ascii=False))
