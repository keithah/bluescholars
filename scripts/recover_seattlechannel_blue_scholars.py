#!/usr/bin/env python3
"""Recover the Seattle Channel Blue Scholars program page and video mementos."""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import requests

from restore.archive import validate_payload

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "recovery/other-archives"
RAW = OUT / "raw"
INDEX = OUT / "seattlechannel-cdx.json"
MANIFEST = OUT / "seattlechannel-recovery.json"
MAX_BYTES = 100_000_000


def recover(delay: float = 1.5) -> dict:
    if delay < 0:
        raise ValueError("delay must be nonnegative")
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {
        "version": 1, "pages": {}, "videos": {}, "payloads": {}}
    RAW.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers["User-Agent"] = "BlueScholarsRestoration/0.1 (historical preservation)"
    failures = []

    for original, rows in index.items():
        kind = "video" if original.endswith(".mp4") else "page"
        bucket = manifest["videos"] if kind == "video" else manifest["pages"]
        for row in rows:
            timestamp, cdx_original, status, mime, digest, length = row
            key = f"{timestamp}:{cdx_original}:{digest}"
            if key in bucket and (ROOT / bucket[key]["raw_path"]).is_file():
                continue
            replay = f"https://web.archive.org/web/{timestamp}id_/{cdx_original}"
            try:
                response = session.get(replay, timeout=(8, 60), stream=True)
                response.raise_for_status()
                content_type = response.headers.get("Content-Type", "").split(";", 1)[0].lower()
                body = bytearray()
                for chunk in response.iter_content(256 * 1024):
                    if chunk:
                        body.extend(chunk)
                        if len(body) > MAX_BYTES:
                            raise ValueError("payload exceeded 100 MB preservation limit")
                payload = bytes(body)
                if kind == "page":
                    validate_payload(payload, "html")
                    suffix = ".html"
                else:
                    if not content_type.startswith("video/") or len(payload) < 12 or payload[4:8] != b"ftyp":
                        raise ValueError(f"response is not a valid MP4 ({content_type})")
                    suffix = ".mp4"
                sha = hashlib.sha256(payload).hexdigest()
                rel = f"recovery/other-archives/raw/{sha}{suffix}"
                path = ROOT / rel
                if not path.exists():
                    path.write_bytes(payload)
                record = {"timestamp": timestamp, "original_url": cdx_original,
                          "cdx_digest": digest, "cdx_length": int(length),
                          "replay_url": replay, "content_type": content_type,
                          "bytes": len(payload), "sha256": sha, "raw_path": rel,
                          "rights_status": "unresolved; local recovery only"}
                bucket[key] = record
                manifest["payloads"].setdefault(sha, {"raw_path": rel, "bytes": len(payload), "kind": kind})
            except Exception as exc:
                failures.append({"timestamp": timestamp, "original_url": cdx_original,
                                 "stage": kind, "error": f"{type(exc).__name__}: {exc}"})
            MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            time.sleep(delay)
    manifest["last_report"] = {
        "page_capture_records": len(manifest["pages"]),
        "video_capture_records": len(manifest["videos"]),
        "unique_payloads": len(manifest["payloads"]),
        "failures_this_run": failures,
        "limitations": ["Wayback results cover only the two exact URLs in the saved CDX query.",
                        "This publisher-hosted content is not part of the original Blue Scholars website.",
                        "Rights remain unresolved; recovered files are not published."]}
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest["last_report"]


if __name__ == "__main__":
    print(json.dumps(recover(), indent=2, ensure_ascii=False))
