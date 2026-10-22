#!/usr/bin/env python3
"""Preserve an audio file explicitly linked from a recovered press page.

Exact Wayback CDX rows, digest-verified media bytes, parent-page provenance,
and rights status are checkpointed separately from the public website.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import time
from pathlib import Path

import requests

from restore.archive import validate_payload

ROOT = Path(__file__).resolve().parents[1]
PRESS = ROOT / "recovery/other-archives/press-articles"
OUT = ROOT / "recovery/other-archives/press-media"
SOURCE = "http://soundscenerevolution.com/podpress_trac/web/147/0/podcast042.mp3"
PAGE = "http://soundscenerevolution.com/2006/12/05/interview-with-blue-scholars-podcast-42/"
CDX = "https://web.archive.org/cdx/search/cdx"
FIELDS = "timestamp,original,statuscode,mimetype,digest,length"
MAX_BYTES = 100_000_000


def cdx_sha1(data: bytes) -> str:
    return base64.b32encode(hashlib.sha1(data).digest()).decode("ascii").rstrip("=")


def recover(delay: float = 1.0, max_files: int = 40) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    media = OUT / "media"
    media.mkdir(exist_ok=True)
    manifest_path = OUT / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {
        "source_page": PAGE,
        "source_media_url": SOURCE,
        "archive": "Internet Archive Wayback",
        "captures": {},
    }
    session = requests.Session()
    session.headers["User-Agent"] = "BlueScholarsHistoricalRecovery/0.1 (source-linked media preservation)"
    report = {
        "source_page": PAGE,
        "source_page_manifest": "recovery/other-archives/press-articles/manifest.json",
        "source_media_url": SOURCE,
        "source_page_exact_wayback_mementos": 0,
        "cdx_rows": 0,
        "attempted": 0,
        "recovered": 0,
        "failures": [],
        "rights_status": "third-party podcast; recovery-only pending rights review",
    }
    try:
        pages = json.loads((PRESS / "manifest.json").read_text())["page_captures"].values()
        report["source_page_exact_wayback_mementos"] = sum(
            1 for row in pages
            if row.get("original_url", "").split("://", 1)[-1].rstrip("/")
            == PAGE.split("://", 1)[-1].rstrip("/")
        )
        response = session.get(CDX, params={
            "url": SOURCE, "matchType": "exact", "output": "json", "fl": FIELDS,
            "filter": "statuscode:200", "limit": 100,
        }, timeout=(10, 50))
        response.raise_for_status()
        rows = response.json()
        rows = rows[1:] if rows else []
        manifest["cdx_rows"] = rows
        manifest["queried_at_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    except Exception as exc:
        report["failures"].append({"stage": "cdx", "url": SOURCE, "error": f"{type(exc).__name__}: {exc}"})
        manifest["last_report"] = report
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
        (OUT / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
        return report

    rows = manifest.get("cdx_rows", [])
    report["cdx_rows"] = len(rows)
    for row in rows:
        if len(row) < 6:
            continue
        timestamp, original, status, mimetype, digest, length = row[:6]
        if status != "200" or not (mimetype.lower().startswith("audio/") or original.lower().endswith(".mp3")):
            continue
        key = f"{original}@@{timestamp}@@{digest}"
        current = manifest["captures"].get(key)
        if current and (ROOT / current.get("raw_path", "")).is_file():
            continue
        if report["attempted"] >= max_files:
            break
        report["attempted"] += 1
        replay = f"https://web.archive.org/web/{timestamp}id_/{original}"
        try:
            response = session.get(replay, timeout=(10, 90), stream=True)
            response.raise_for_status()
            body = bytearray()
            for chunk in response.iter_content(256 * 1024):
                if chunk:
                    body.extend(chunk)
                    if len(body) > MAX_BYTES:
                        raise ValueError("media exceeds 100 MB cap")
            data = bytes(body)
            validate_payload(data, "media")
            actual = cdx_sha1(data)
            if digest and actual != digest:
                raise ValueError(f"CDX SHA-1 mismatch: {actual} != {digest}")
            sha256 = hashlib.sha256(data).hexdigest()
            path = media / f"{sha256}.mp3"
            if not path.exists():
                path.write_bytes(data)
            manifest["captures"][key] = {
                "source_page_url": PAGE,
                "source_media_url": SOURCE,
                "timestamp": timestamp,
                "replay_url": replay,
                "cdx_mimetype": mimetype,
                "cdx_digest": digest,
                "cdx_sha1_verified": bool(digest),
                "cdx_length": int(length),
                "bytes": len(data),
                "sha256": sha256,
                "raw_path": path.relative_to(ROOT).as_posix(),
                "rights_status": "unreviewed; local-only",
            }
            report["recovered"] += 1
        except Exception as exc:
            report["failures"].append({
                "stage": "replay", "url": original, "timestamp": timestamp,
                "error": f"{type(exc).__name__}: {exc}",
            })
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
        time.sleep(delay)

    report["capture_records_total"] = len(manifest["captures"])
    report["unique_payload_hashes_total"] = len({row["sha256"] for row in manifest["captures"].values()})
    report["publication_status"] = "local-only pending rights review"
    manifest["last_report"] = report
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    (OUT / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--max-files", type=int, default=40)
    args = parser.parse_args()
    print(json.dumps(recover(args.delay, args.max_files), indent=2, ensure_ascii=False))
