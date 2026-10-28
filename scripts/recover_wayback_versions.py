#!/usr/bin/env python3
"""Recover distinct Wayback HTML revisions already discovered in CDX.

This is a recovery-only workflow: it stores raw source pages and provenance,
stops on archive rate limits, and checkpoints each successful replay.
"""
from __future__ import annotations

from restore.cooldown import ArchiveCooldown, RecoverySession
import argparse
import base64
import hashlib
import json
import time
from pathlib import Path

import requests

from restore.archive import validate_payload

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "recovery/wayback-related/manifest.json"
OUT = ROOT / "recovery/wayback-versions"
MAX_BYTES = 25_000_000


def cdx_sha1_base32(payload: bytes) -> str:
    """Return the Internet Archive CDX SHA-1 digest representation."""
    return base64.b32encode(hashlib.sha1(payload).digest()).decode("ascii").rstrip("=")


def recover(contains: str, before: str = "", after: str = "", max_files: int = 20,
            delay: float = 1.0, retry_failed: bool = False) -> dict:
    if max_files < 1 or delay < 0:
        raise ValueError("max_files must be positive and delay nonnegative")
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "raw").mkdir(exist_ok=True)
    manifest_path = OUT / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {
        "version": 1, "revisions": {}}
    revisions = manifest.setdefault("revisions", {})
    failures = manifest.setdefault("failures", {})
    needle = contains.casefold()
    candidates = []
    for original, index in source.get("indexes", {}).items():
        if needle not in original.casefold():
            continue
        for row in index.get("cdx_rows", []):
            if len(row) < 6 or row[2] != "200" or row[3].lower() not in ("text/html", "application/xhtml+xml"):
                continue
            stamp = row[0]
            if before and stamp[:4] >= before:
                continue
            if after and stamp[:4] < after:
                continue
            candidates.append({"original_url": original, "timestamp": stamp, "status": row[2],
                               "mime": row[3], "cdx_digest": row[4], "cdx_length": row[5]})
    # One sample per archived digest is sufficient to recover a distinct page
    # body; the full timestamp-level index remains in the parent checkpoint.
    distinct = {}
    for record in sorted(candidates, key=lambda r: r["timestamp"]):
        key = f'{record["original_url"]}@@{record["cdx_digest"]}'
        distinct.setdefault(key, record)
    pending = [(key, record) for key, record in distinct.items()
               if (key not in revisions or not (ROOT / revisions[key].get("raw_path", "")).is_file())
               and (retry_failed or key not in failures)]
    report = {"archive": "Internet Archive Wayback", "source_index": str(SOURCE.relative_to(ROOT)),
              "url_filter": contains, "after_year_inclusive": after or None,
              "before_year_exclusive": before or None, "candidate_mementos": len(candidates),
              "distinct_cdx_revisions": len(distinct), "pending_before_batch": len(pending),
              "previous_failures_skipped": len(set(distinct) & set(failures)) if not retry_failed else 0,
              "attempted": 0, "recovered": 0, "failures": [], "rate_limited": False,
              "limitations": ["Distinct CDX digests are sampled once per original URL; timestamp-level coverage remains in the parent CDX manifest.",
                              "All pages stay in recovery-only storage pending content, relevance, compatibility and rights review."]}
    session = RecoverySession()
    session.headers["User-Agent"] = "BlueScholarsRestoration/0.1 (historical preservation)"
    for key, record in pending:
        if report["attempted"] >= max_files:
            break
        report["attempted"] += 1
        replay = f'https://web.archive.org/web/{record["timestamp"]}id_/{record["original_url"]}'
        try:
            response = session.get(replay, timeout=(8, 45), stream=True)
            if response.status_code == 429:
                report["failures"].append({**record, "stage": "replay", "error": "HTTP 429; stopped to respect Wayback rate limit"})
                report["rate_limited"] = True
                break
            response.raise_for_status()
            body = bytearray()
            for chunk in response.iter_content(128 * 1024):
                body.extend(chunk)
                if len(body) > MAX_BYTES:
                    raise ValueError("memento exceeded 25 MB limit")
            payload = bytes(body)
            validate_payload(payload, "html")
            digest = hashlib.sha256(payload).hexdigest()
            actual_cdx_digest = cdx_sha1_base32(payload)
            digest_verified = actual_cdx_digest == record["cdx_digest"]
            raw_path = f"recovery/wayback-versions/raw/{digest}.html"
            destination = ROOT / raw_path
            if not destination.exists():
                destination.write_bytes(payload)
            revisions[key] = {**record, "sha256": digest, "bytes": len(payload),
                              "actual_cdx_digest": actual_cdx_digest,
                              "cdx_digest_verified": digest_verified,
                              "verification_status": "cdx_sha1_match" if digest_verified else "cdx_sha1_mismatch",
                              "response_mime": response.headers.get("Content-Type", ""),
                              "raw_path": raw_path, "raw_replay_url": replay,
                              "review_required_before_publication": True}
            report["recovered"] += 1
        except ArchiveCooldown:
            raise
        except Exception as exc:
            failure = {**record, "stage": "replay", "error": f"{type(exc).__name__}: {exc}"}
            report["failures"].append(failure)
            failures[key] = failure
        manifest["last_report"] = report
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        time.sleep(delay)
    report["revision_records_total"] = len(revisions)
    report["failure_records_total"] = len(failures)
    report["unique_payloads_total"] = len({r["sha256"] for r in revisions.values() if r.get("sha256")})
    report["cdx_sha1_matches_total"] = sum(1 for r in revisions.values() if r.get("cdx_digest_verified") is True)
    report["cdx_sha1_mismatches_total"] = sum(1 for r in revisions.values() if r.get("cdx_digest_verified") is False)
    report["legacy_unverified_total"] = sum(1 for r in revisions.values() if "cdx_digest_verified" not in r)
    report["pending_after_batch"] = max(0, len(pending) - report["attempted"])
    manifest["last_report"] = report
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (OUT / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contains", required=True, help="case-insensitive substring of an indexed original URL")
    parser.add_argument("--after-year", default="", help="include captures from this year onward")
    parser.add_argument("--before-year", default="", help="exclude captures from this year onward")
    parser.add_argument("--max-files", type=int, default=20)
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--retry-failed", action="store_true", help="retry previously failed replay requests")
    args = parser.parse_args()
    print(json.dumps(recover(args.contains, args.before_year, args.after_year, args.max_files, args.delay,
                             args.retry_failed),
                     indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
