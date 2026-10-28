#!/usr/bin/env python3
"""Preserve KEXP's source-linked 2014 Blue Scholars photo gallery evidence."""
from __future__ import annotations

from restore.cooldown import ArchiveCooldown, RecoverySession
import base64
import hashlib
import json
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from restore.archive import validate_payload

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "recovery/other-archives"
RAW = OUT / "raw"
CDX = OUT / "kexp-fremont-gallery-cdx.json"
MANIFEST = OUT / "kexp-fremont-gallery-recovery.json"
PAGE_URL = "https://www.kexp.org/read/2014/6/26/photo-gallery-fremont-fair-solstice-concert-series-621/"


def _sha1_cdx(payload: bytes) -> str:
    return base64.b32encode(hashlib.sha1(payload).digest()).decode("ascii").rstrip("=")


def recover(delay: float = 1.0) -> dict:
    if delay < 0:
        raise ValueError("delay must be nonnegative")
    index = json.loads(CDX.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {
        "version": 1, "pages": {}, "images": {}}
    RAW.mkdir(parents=True, exist_ok=True)
    session = RecoverySession()
    session.headers["User-Agent"] = "BlueScholarsRestoration/0.1 (historical preservation)"
    failures = []

    for row in index.get(PAGE_URL, []):
        timestamp, original, _status, _mime, cdx_digest, cdx_length = row
        key = f"{timestamp}:{original}:{cdx_digest}"
        if key in manifest["pages"] and (ROOT / manifest["pages"][key]["raw_path"]).is_file():
            continue
        replay = f"https://web.archive.org/web/{timestamp}id_/{original}"
        try:
            response = session.get(replay, timeout=(8, 45))
            response.raise_for_status()
            payload = response.content
            validate_payload(payload, "html")
            sha = hashlib.sha256(payload).hexdigest()
            if _sha1_cdx(payload) != cdx_digest:
                raise ValueError("replayed HTML SHA-1 does not match the CDX digest")
            rel = f"recovery/other-archives/raw/{sha}.html"
            (ROOT / rel).write_bytes(payload)
            manifest["pages"][key] = {"timestamp": timestamp, "original_url": original,
                "replay_url": replay, "cdx_digest": cdx_digest, "cdx_length": int(cdx_length),
                "bytes": len(payload), "sha256": sha, "raw_path": rel,
                "rights_status": "KEXP page; local recovery only"}
        except ArchiveCooldown:
            raise
        except Exception as exc:
            failures.append({"stage": "wayback_page", "url": replay,
                             "error": f"{type(exc).__name__}: {exc}"})
        MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        time.sleep(delay)

    page = session.get(PAGE_URL, timeout=(8, 30))
    page.raise_for_status()
    html_bytes = page.content
    validate_payload(html_bytes, "html")
    page_sha = hashlib.sha256(html_bytes).hexdigest()
    page_path = ROOT / "recovery/other-archives/raw" / f"{page_sha}.html"
    page_path.write_bytes(html_bytes)
    soup = BeautifulSoup(html_bytes, "html.parser")
    images = soup.find_all("img", title="Blue Scholars")
    for image in images:
        url = image.get("src") or image.get("data-src")
        if not url:
            continue
        label = image.parent.get_text(" ", strip=True)
        if url in manifest["images"] and (ROOT / manifest["images"][url]["raw_path"]).is_file():
            continue
        try:
            response = session.get(url, timeout=(8, 45))
            response.raise_for_status()
            payload = response.content
            validate_payload(payload, "image")
            if not response.headers.get("Content-Type", "").lower().startswith("image/"):
                raise ValueError("response content type is not an image")
            sha = hashlib.sha256(payload).hexdigest()
            suffix = ".jpg" if payload.startswith(b"\xff\xd8\xff") else ".img"
            rel = f"recovery/other-archives/raw/{sha}{suffix}"
            (ROOT / rel).write_bytes(payload)
            manifest["images"][url] = {"original_url": url, "caption_and_credit": label,
                "bytes": len(payload), "sha256": sha, "content_type": response.headers.get("Content-Type"),
                "raw_path": rel,
                "category": "band-performance" if label.startswith("Blue Scholars /") else "gallery-context",
                "wayback_exact_url_rows": 0 if label.startswith("Blue Scholars /") else None,
                "rights_status": "photographer credited by KEXP; redistribution license not established; local-only"}
        except ArchiveCooldown:
            raise
        except Exception as exc:
            failures.append({"stage": "source_image", "url": url,
                             "error": f"{type(exc).__name__}: {exc}"})
        MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        time.sleep(delay)

    for record in manifest["images"].values():
        is_band = str(record.get("caption_and_credit", "")).startswith("Blue Scholars /")
        record["category"] = "band-performance" if is_band else "gallery-context"
        if not is_band:
            record["wayback_exact_url_rows"] = None

    manifest["current_page"] = {"source_url": PAGE_URL, "title": "Photo Gallery: Fremont Fair Solstice Concert Series 6/21",
        "published_date": "2014-06-26", "bytes": len(html_bytes), "sha256": page_sha,
        "raw_path": str(page_path.relative_to(ROOT)),
        "captioned_band_images": sum(image.parent.get_text(" ", strip=True).startswith("Blue Scholars /") for image in images),
        "source_kind": "current KEXP page with historical article date"}
    manifest["last_report"] = {"wayback_page_captures": len(manifest["pages"]),
        "unique_archived_pages": len({x["sha256"] for x in manifest["pages"].values()}),
        "captioned_band_image_records": sum(x.get("category") == "band-performance" for x in manifest["images"].values()),
        "contextual_gallery_image_records": sum(x.get("category") == "gallery-context" for x in manifest["images"].values()),
        "all_saved_image_records": len(manifest["images"]),
        "unique_image_payloads": len({x["sha256"] for x in manifest["images"].values()}),
        "failures_this_run": failures,
        "limitations": ["No exact Wayback image mementos were indexed for the five article images.",
                        "Image bytes were retrieved from the image URLs embedded in KEXP's page, not Wayback.",
                        "Photographer credits are preserved, but a redistribution license was not found; files remain local-only."]}
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest["last_report"]


if __name__ == "__main__":
    print(json.dumps(recover(), indent=2, ensure_ascii=False))
