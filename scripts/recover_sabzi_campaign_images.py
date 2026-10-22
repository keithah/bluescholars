#!/usr/bin/env python3
"""Recover Wayback image revisions linked by the archived Townfolk Pho pages.

Every URL index, distinct image digest, replay result and source-page reference
is checkpointed locally. This is a recovery-only workflow; nothing is promoted
to the restored site.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import requests
from bs4 import BeautifulSoup

from restore.archive import validate_payload

ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / "recovery/other-archives/sabzi-townfolk-pages.json"
OUT = ROOT / "recovery/other-archives"
CDX = "https://web.archive.org/cdx/search/cdx"
FIELDS = "timestamp,original,statuscode,mimetype,digest,length"
MAX_BYTES = 25_000_000


def candidates() -> dict[str, dict]:
    manifest = json.loads(PAGES.read_text(encoding="utf-8"))
    result: dict[str, dict] = {}
    for page in manifest.get("captures", []):
        if page.get("kind") != "html" or page.get("status") != "recovered_local_only":
            continue
        path = ROOT / page.get("raw_path", "")
        if not path.is_file():
            continue
        soup = BeautifulSoup(path.read_bytes(), "html.parser")
        for node in soup.find_all("img"):
            value = node.get("src") or node.get("data-src")
            if not value:
                continue
            url = urljoin(page["original_url"], value)
            parts = urlsplit(url)
            if parts.scheme not in ("http", "https") or not parts.path.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp")):
                continue
            ref = {"page_url": page["original_url"], "page_timestamp": page["timestamp"],
                   "page_title": (soup.title.get_text(" ", strip=True) if soup.title else ""),
                   "alt": node.get("alt", "")}
            record = result.setdefault(url, {"original_url": url, "referrers": [], "alt_texts": []})
            if ref not in record["referrers"]:
                record["referrers"].append(ref)
            if ref["alt"] and ref["alt"] not in record["alt_texts"]:
                record["alt_texts"].append(ref["alt"])
    return result


def sha1_digest(body: bytes) -> str:
    return base64.b32encode(hashlib.sha1(body).digest()).decode("ascii").rstrip("=")


def recover(delay: float = 0.75, max_urls: int = 100, max_files: int = 200,
            replay_only: bool = False) -> dict:
    if delay < 0 or max_urls < 1 or max_files < 1:
        raise ValueError("delay must be nonnegative and limits must be positive")
    OUT.mkdir(parents=True, exist_ok=True)
    raw_dir = OUT / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = OUT / "sabzi-townfolk-assets.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {
        "version": 1, "archive": "Internet Archive Wayback", "assets": {}}
    assets = manifest.setdefault("assets", {})
    found = candidates()
    for url, lead in found.items():
        existing = assets.setdefault(url, {**lead, "cdx_rows": [], "revisions": {}})
        existing["referrers"] = lead["referrers"]
        existing["alt_texts"] = lead["alt_texts"]

    session = requests.Session()
    session.headers["User-Agent"] = "BlueScholarsRestoration/0.1 (historical preservation)"
    report = {"source_pages": str(PAGES.relative_to(ROOT)), "candidate_images": len(found),
              "queried": 0, "image_mementos": 0, "attempted_replays": 0,
              "recovered_records": 0, "unique_payloads": 0, "failures": [],
              "rate_limited": False, "limitations": [
                  "Only image URLs explicitly referenced by saved Townfolk campaign HTML were checked.",
                  "All source-linked assets remain local-only pending rights review."]}

    # First persist all CDX rows. Existing results survive interruptions.
    for url, item in ([] if replay_only else list(assets.items())[:max_urls]):
        # An empty result is still a completed exact-URL query. Do not repeat
        # it on every resume; only explicit transient failures become retryable.
        if "queried_at" in item:
            continue
        retry_after = item.get("query_retry_after")
        if item.get("query_error") and retry_after:
            try:
                if datetime.fromisoformat(retry_after) > datetime.now(timezone.utc):
                    continue
            except ValueError:
                pass
        try:
            response = session.get(CDX, params={"url": url, "matchType": "exact", "output": "json",
                "fl": FIELDS, "filter": "statuscode:200", "limit": 200}, timeout=(10, 45))
            if response.status_code == 429:
                report["rate_limited"] = True
                item["query_error"] = "HTTP 429; stopped to respect Wayback rate limit"
                item["query_retry_after"] = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
                report["failures"].append({"url": url, "stage": "cdx", "error": item["query_error"]})
                manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                break
            response.raise_for_status()
            data = response.json()
            rows = data[1:] if data else []
            item["cdx_rows"] = rows
            item["image_mementos"] = [row for row in rows if len(row) > 5 and row[2] == "200" and row[3].lower().startswith("image/")]
            item["queried_at"] = datetime.utcnow().isoformat() + "Z"
            item.pop("query_error", None)
            item.pop("query_retry_after", None)
            report["queried"] += 1
        except Exception as exc:
            item["query_error"] = f"{type(exc).__name__}: {exc}"
            item["query_retry_after"] = (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()
            report["failures"].append({"url": url, "stage": "cdx", "error": item["query_error"]})
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if report["rate_limited"]:
            break
        time.sleep(delay)

    pending: list[tuple[str, str, list[str], list[str]]] = []
    for url, item in assets.items():
        rows = item.get("image_mementos", [])
        report["image_mementos"] += len(rows)
        groups: dict[str, list[list[str]]] = {}
        for row in rows:
            groups.setdefault(row[4], []).append(row)
        for digest, variants in groups.items():
            # Select the capture closest to a page that explicitly references
            # the asset. Keep every timestamp sharing the selected digest.
            refs = item.get("referrers", [])
            def distance(row: list[str]) -> int:
                stamps = [r.get("page_timestamp", "") for r in refs]
                return min((abs(int(row[0]) - int(stamp)) for stamp in stamps
                            if row[0].isdigit() and stamp.isdigit()), default=10**30)
            selected = min(variants, key=distance)
            key = f"{url}@@wayback:{selected[0]}:{digest}"
            existing = item.setdefault("revisions", {}).get(key, {})
            if existing.get("status") == "recovered" and (ROOT / existing.get("raw_path", "")).is_file():
                continue
            pending.append((url, key, selected, [r[0] for r in variants]))

    for url, key, row, equivalent_timestamps in pending:
        if report["attempted_replays"] >= max_files or report["rate_limited"]:
            break
        report["attempted_replays"] += 1
        timestamp, original, _, mime, cdx_digest, cdx_length = row
        replay = f"https://web.archive.org/web/{timestamp}id_/{original}"
        record = {"original_url": original, "timestamp": timestamp, "cdx_mime": mime,
                  "cdx_digest": cdx_digest, "cdx_length": cdx_length,
                  "same_digest_timestamps": equivalent_timestamps, "replay_url": replay,
                  "referrers": assets[url].get("referrers", []), "alt_texts": assets[url].get("alt_texts", [])}
        try:
            response = session.get(replay, timeout=(10, 60), stream=True)
            if response.status_code == 429:
                report["rate_limited"] = True
                raise RuntimeError("HTTP 429; stopped to respect Wayback rate limit")
            response.raise_for_status()
            body = bytearray()
            for chunk in response.iter_content(128 * 1024):
                body.extend(chunk)
                if len(body) > MAX_BYTES:
                    raise ValueError("image memento exceeded 25 MB limit")
            payload = bytes(body)
            validate_payload(payload, "image")
            if sha1_digest(payload) != cdx_digest:
                raise ValueError("replayed bytes do not match CDX SHA-1 digest")
            sha256 = hashlib.sha256(payload).hexdigest()
            suffix = Path(urlsplit(original).path).suffix.lower() or ".bin"
            raw_path = Path("recovery/other-archives/raw") / f"{sha256}{suffix}"
            destination = ROOT / raw_path
            if not destination.exists():
                destination.write_bytes(payload)
            record.update({"sha256": sha256, "cdx_sha1_verified": sha1_digest(payload) == cdx_digest,
                           "bytes": len(payload), "response_mime": response.headers.get("Content-Type", ""),
                           "raw_path": raw_path.as_posix(), "status": "recovered",
                           "review_required_before_publication": True})
            report["recovered_records"] += 1
        except Exception as exc:
            record.update({"status": "failed", "error": f"{type(exc).__name__}: {exc}"})
            report["failures"].append({"url": original, "timestamp": timestamp, "stage": "replay", "error": record["error"]})
        assets[url].setdefault("revisions", {})[key] = record
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if report["rate_limited"]:
            break
        time.sleep(delay)

    records = [r for item in assets.values() for r in item.get("revisions", {}).values()]
    report["asset_urls_indexed"] = len(assets)
    report["capture_records_total"] = len(records)
    report["validated_capture_records_total"] = sum(r.get("status") == "recovered" for r in records)
    report["unique_payloads_total"] = len({r["sha256"] for r in records if r.get("status") == "recovered"})
    report["pending_revisions"] = sum(1 for item in assets.values()
        for digest in {r[4] for r in item.get("image_mementos", [])}
        if not any(x.get("cdx_digest") == digest and x.get("status") == "recovered"
                   for x in item.get("revisions", {}).values()))
    manifest["last_report"] = report
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (OUT / "sabzi-townfolk-assets-report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--delay", type=float, default=0.75)
    parser.add_argument("--max-urls", type=int, default=100)
    parser.add_argument("--max-files", type=int, default=200)
    parser.add_argument("--replay-only", action="store_true",
                        help="replay already indexed captures without requesting more CDX rows")
    args = parser.parse_args()
    print(json.dumps(recover(args.delay, args.max_urls, args.max_files, args.replay_only), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
