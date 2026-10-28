#!/usr/bin/env python3
"""Preserve public photographer-hosted copies of images linked from the 2011 party story.

These are current publisher-hosted copies, not Wayback mementos. Originals stay
in ignored local recovery storage and require rights review before publication.
"""
from __future__ import annotations

from restore.cooldown import ArchiveCooldown, RecoverySession
import hashlib
import json
import re
import struct
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

import requests

from restore.archive import validate_payload

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "recovery/other-archives/photographer/manifest.json"
OUT = ROOT / "recovery/other-archives/photographer/current-images"
MAX_BYTES = 25_000_000


def candidates() -> list[dict]:
    page_manifest = json.loads(SOURCE.read_text(encoding="utf-8"))
    by_smugmug_id: dict[str, list[dict]] = {}
    armin = {}
    for capture in page_manifest.get("captures", {}).values():
        for image in capture.get("images", []):
            url = image.get("url", "")
            path = urlsplit(url).path
            if not ("blue-scholars-061511" in path.lower() or "geosabzi" in path.lower()):
                continue
            if "arminausejo.com/wp-content/uploads/2011/06/" in url and "blue-scholars-061511" in path.lower():
                if re.search(r"-\d+x\d+(?=\.[a-zA-Z0-9]+$)", path):
                    continue
                armin[url] = {"url": url, "page_title": capture.get("title", ""),
                              "page_url": capture.get("original_url", ""), "timestamp": capture.get("timestamp")}
            elif "smugmug.com" in url:
                match = re.search(r"/i-([A-Za-z0-9]+)/", path)
                if not match:
                    continue
                size_rank = 3 if re.search(r"/(O|X[1-5])(?:/|$)", path) else 2 if "/XL/" in path else 1
                by_smugmug_id.setdefault(match.group(1), []).append({"url": url, "size_rank": size_rank,
                    "page_title": capture.get("title", ""), "page_url": capture.get("original_url", ""),
                    "timestamp": capture.get("timestamp")})
    selected = list(armin.values())
    for photo_id, variants in by_smugmug_id.items():
        choice = max(variants, key=lambda x: (x["size_rank"], len(x["url"])))
        choice["photo_id"] = photo_id
        choice["source_variants_observed"] = sorted({x["url"] for x in variants})
        selected.append(choice)
    return selected


def dimensions(payload: bytes) -> list[int] | None:
    """Read raster dimensions from common formats without image libraries."""
    if payload.startswith(b"\x89PNG\r\n\x1a\n") and len(payload) >= 24:
        return list(struct.unpack(">II", payload[16:24]))
    if payload.startswith((b"GIF87a", b"GIF89a")) and len(payload) >= 10:
        return list(struct.unpack("<HH", payload[6:10]))
    if payload.startswith(b"RIFF") and payload[8:12] == b"WEBP" and payload[12:16] == b"VP8X" and len(payload) >= 30:
        return [1 + int.from_bytes(payload[24:27], "little"), 1 + int.from_bytes(payload[27:30], "little")]
    if payload.startswith(b"\xff\xd8"):
        offset = 2
        while offset + 9 < len(payload):
            if payload[offset] != 0xFF:
                offset += 1
                continue
            marker = payload[offset + 1]
            offset += 2
            if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
                continue
            if offset + 2 > len(payload):
                break
            length = int.from_bytes(payload[offset:offset + 2], "big")
            if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                if offset + 7 <= len(payload):
                    height = int.from_bytes(payload[offset + 3:offset + 5], "big")
                    width = int.from_bytes(payload[offset + 5:offset + 7], "big")
                    return [width, height]
                break
            if length < 2:
                break
            offset += length
    return None


def recover(delay: float = 0.5, limit: int = 100) -> dict:
    if delay < 0 or limit < 1:
        raise ValueError("delay must be nonnegative and limit positive")
    OUT.mkdir(parents=True, exist_ok=True)
    raw = OUT / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    manifest_path = OUT / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {
        "version": 1, "source_page_manifest": str(SOURCE.relative_to(ROOT)), "source_kind": "current publisher-hosted image copy",
        "images": {}}
    choices = candidates()
    session = RecoverySession()
    session.headers["User-Agent"] = "BlueScholarsHistoricalRecovery/0.1 (source preservation)"
    report = {"candidate_photo_urls": len(choices), "attempted": 0, "recovered": 0,
              "downloaded_bytes": 0, "failures": [], "rights_status": "review_required_before_publication",
              "limitations": ["Current image bytes are labeled separately from archived mementos.",
                              "Only image URLs explicitly present in captured photographer pages were selected.",
                              "No asset is promoted to the public restoration."]}
    for item in choices:
        url = item["url"]
        if url in manifest["images"] and (ROOT / manifest["images"][url].get("raw_path", "")).is_file():
            continue
        if report["attempted"] >= limit:
            break
        report["attempted"] += 1
        try:
            with session.get(url, timeout=(8, 45), stream=True) as response:
                response.raise_for_status()
                content_type = response.headers.get("Content-Type", "").split(";", 1)[0].lower()
                if not content_type.startswith("image/"):
                    raise ValueError(f"expected image content type, got {content_type}")
                body = bytearray()
                for chunk in response.iter_content(128 * 1024):
                    if chunk:
                        body.extend(chunk)
                        if len(body) > MAX_BYTES:
                            raise ValueError("image exceeded 25 MB cap")
            payload = bytes(body)
            validate_payload(payload, "image")
            dimensions_found = dimensions(payload)
            sha256 = hashlib.sha256(payload).hexdigest()
            suffix = Path(urlsplit(url).path).suffix.lower() or ".img"
            path = raw / f"{sha256}{suffix}"
            if not path.exists():
                path.write_bytes(payload)
            manifest["images"][url] = {**item, "source_url": url, "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "source_kind": "current publisher-hosted copy; not an archive memento", "bytes": len(payload),
                "sha256": sha256, "raw_path": path.relative_to(ROOT).as_posix(), "content_type": content_type,
                "dimensions": dimensions_found, "rights_status": "review_required_before_publication"}
            report["recovered"] += 1
            report["downloaded_bytes"] += len(payload)
        except ArchiveCooldown:
            raise
        except Exception as exc:
            manifest["images"][url] = {**item, "source_url": url,
                "status": "failed", "error": f"{type(exc).__name__}: {exc}",
                "rights_status": "review_required_before_publication"}
            report["failures"].append({"url": url, "error": manifest["images"][url]["error"]})
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        time.sleep(delay)
    report["image_records"] = len(manifest["images"])
    report["unique_payloads"] = len({x["sha256"] for x in manifest["images"].values() if x.get("sha256")})
    manifest["last_report"] = report
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (OUT / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--delay", type=float, default=0.5)
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()
    print(json.dumps(recover(args.delay, args.limit), indent=2, ensure_ascii=False))
