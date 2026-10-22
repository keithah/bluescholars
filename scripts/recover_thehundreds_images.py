#!/usr/bin/env python3
"""Preserve image files still served at URLs embedded in The Hundreds archive pages.

These are live-origin copies, not Wayback mementos. The script saves a small
source-linked set locally with response metadata and SHA-256 provenance; it
does not promote or publish the third-party files.
"""
from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "recovery/other-archives/thehundreds"
PAGE = "https://thehundreds.com/blogs/content/food-and-sh-t"
IMAGE_URLS = [
    f"https://storage.googleapis.com/thehundreds/media/2015/02/foodandshit_prometheus-brown_thehundreds{i:02d}.jpg"
    for i in (1, 2, 3, 7, 8, 16, 17)
]
MAX_BYTES = 25_000_000


def recover(delay: float = 1.0) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    image_dir = OUT / "images"
    image_dir.mkdir(exist_ok=True)
    manifest_path = OUT / "image-manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {
        "source_page": PAGE,
        "archive_status": "No exact Wayback CDX rows for the 11 image URL variants exposed by archived article pages.",
        "items": {},
    }
    session = requests.Session()
    session.headers["User-Agent"] = "BlueScholarsRestoration/0.1 (historical preservation research)"
    for url in IMAGE_URLS:
        if url in manifest["items"]:
            item = manifest["items"][url]
            if (ROOT / item.get("local_path", "__missing__")).is_file():
                continue
        record = {"source_image_url": url, "source_page": PAGE, "source_page_capture": "Wayback-preserved article HTML; image URL embedded there"}
        try:
            response = session.get(url, timeout=(10, 35))
            response.raise_for_status()
            body = response.content
            if len(body) > MAX_BYTES:
                raise ValueError(f"image exceeds {MAX_BYTES} byte limit")
            if not body.startswith(b"\xff\xd8\xff"):
                raise ValueError("response is not a JPEG by signature")
            sha256 = hashlib.sha256(body).hexdigest()
            name = f"{url.rsplit('thehundreds', 1)[-1].split('.')[0].strip('_')}-{sha256}.jpg"
            local = image_dir / name
            local.write_bytes(body)
            record.update({
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "source_type": "Current response from the original image host; not an archived memento.",
                "http_status": response.status_code,
                "final_url": response.url,
                "content_type": response.headers.get("Content-Type"),
                "last_modified": response.headers.get("Last-Modified"),
                "etag": response.headers.get("ETag"),
                "bytes": len(body),
                "sha256": sha256,
                "local_path": str(local.relative_to(ROOT)),
                "rights_status": "Unreviewed third-party editorial photograph; recovery-only, local-only, not published.",
            })
        except Exception as exc:  # keep each source checkpoint even on partial failures
            record.update({"retrieved_at": datetime.now(timezone.utc).isoformat(), "error": f"{type(exc).__name__}: {exc}"})
        manifest["items"][url] = record
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
        time.sleep(delay)
    manifest["result"] = {
        "queried_urls": len(IMAGE_URLS),
        "saved_files": sum(bool(x.get("local_path") and (ROOT / x["local_path"]).is_file()) for x in manifest["items"].values()),
        "all_local_only": True,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    return manifest


if __name__ == "__main__":
    print(json.dumps(recover(), indent=2, ensure_ascii=False))
