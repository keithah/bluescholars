#!/usr/bin/env python3
"""Inventory and checksum-verify dated Twitter profile captures per handle."""
from __future__ import annotations

from restore.cooldown import ArchiveCooldown, RecoverySession
import argparse
import base64
import hashlib
import json
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
CDX = "https://web.archive.org/cdx/search/cdx"
ACCOUNTS = {
    "prometheusbrown": "Prometheus Brown",
    "bluescholars": "Blue Scholars",
    "sabzi": "Sabzi",
    "wongweezy": "Wong Weezy",
    "canhsolo": "Canh Solo",
}
MAX_BYTES = 25_000_000


def cdx_sha1(payload: bytes) -> str:
    return base64.b32encode(hashlib.sha1(payload).digest()).decode("ascii").rstrip("=")


def recover(accounts: list[str], max_files: int = 100, delay: float = 0.3,
            timeout: int = 45, retry_failed: bool = False) -> dict:
    if max_files < 1 or delay < 0 or timeout < 1:
        raise ValueError("max_files and timeout must be positive; delay must be nonnegative")
    session = RecoverySession()
    session.headers["User-Agent"] = "BlueScholarsRestoration/1.0 (historical preservation)"
    reports = {}
    attempted_total = 0
    for handle in accounts:
        if handle not in ACCOUNTS:
            raise ValueError(f"Unsupported account: {handle}")
        directory = ROOT / f"recovery/twitter-{handle}"
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "raw").mkdir(exist_ok=True)
        index_path = directory / "cdx.json"
        manifest_path = directory / "manifest.json"
        query_urls = [f"twitter.com/{handle}", f"mobile.twitter.com/{handle}", f"x.com/{handle}"]
        try:
            inventories = []
            for query_url in query_urls:
                query = {"url": query_url, "output": "json",
                         "filter": ["statuscode:200", "mimetype:text/html"],
                         "fl": "timestamp,original,statuscode,mimetype,digest,length"}
                response = session.get(CDX, params=query, timeout=(8, timeout))
                response.raise_for_status()
                table = response.json()
                fields = ["timestamp", "original", "statuscode", "mimetype", "digest", "length"]
                if table == []:
                    table = [fields]
                if table[0] != fields:
                    raise ValueError(f"Unexpected CDX response columns for {query_url}")
                inventories.append({"query": query, "query_url": response.url,
                                    "rows": [row for row in table[1:] if len(row) >= 6]})
                time.sleep(min(delay, 0.5))
            row_map = {}
            for inventory in inventories:
                for row in inventory["rows"]:
                    row_map[(row[0], row[1], row[4])] = row
            rows = sorted(row_map.values(), key=lambda row: (row[0], row[1], row[4]))
            timestamp_counts = {}
            for row in rows:
                timestamp_counts[row[0]] = timestamp_counts.get(row[0], 0) + 1
            for row in rows:
                host = row[1].split("/", 3)[2].lower() if "://" in row[1] else "twitter.com"
                variant = "mobile" if host.startswith("mobile.") else "x" if host == "x.com" else "twitter"
                if timestamp_counts[row[0]] > 1:
                    suffix = hashlib.sha256((row[1] + row[4]).encode()).hexdigest()[:6]
                    row.append(f"{row[0]}-{variant}-{suffix}")
                else:
                    row.append(row[0])
            index = {"source": "Internet Archive CDX", "queried_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                     "queries": inventories, "fields": ["timestamp", "original", "statuscode", "mimetype", "digest", "length", "route_id"],
                     "rows": rows}
            index_path.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n")
        except ArchiveCooldown:
            raise
        except Exception as exc:
            reports[handle] = {"status": "index_failed", "error": f"{type(exc).__name__}: {exc}"}
            continue

        old = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
        previous = {(str(item.get("timestamp")), str(item.get("original")), str(item.get("digest"))): item
                    for item in old.get("captures", [])}
        captures = []
        for row in rows:
            stamp, original, status, mimetype, digest, length, route_id = row[:7]
            entry = previous.get((stamp, original, digest), {})
            captures.append({**entry, "timestamp": stamp, "original": original,
                             "route_id": route_id,
                             "statuscode": status, "mimetype": mimetype,
                             "digest": digest, "length": int(length) if str(length).isdigit() else None,
                             "fetch": entry.get("fetch", {"status": "pending"})})
        manifest = {**old, "archive": "Internet Archive Wayback", "account": handle,
                    "display_name": ACCOUNTS[handle], "profile": f"https://twitter.com/{handle}",
                    "inventory_method": "Exact account URL through Internet Archive CDX; all status-200 HTML rows, preserving repeated timestamps",
                    "inventory_queried_at": index["queried_at"], "inventory_count": len(rows),
                    "captures": captures, "assets": old.get("assets", []),
                    "notes": ["Each dated row is retained. Raw bytes are stored only when the replay matches its CDX SHA-1 digest.",
                              "Twitter/X account names and displayed content are captured evidence, not proof of account ownership at every later date."]}
        recovered = 0
        failures = 0
        stopped = False
        for item in captures:
            fetch = item["fetch"]
            local = directory / str(fetch.get("path", "")) if fetch.get("path") else None
            if fetch.get("status") == "recovered" and local and local.is_file():
                continue
            if fetch.get("status") == "failed" and not retry_failed:
                continue
            if attempted_total >= max_files:
                break
            attempted_total += 1
            replay = f"https://web.archive.org/web/{item['timestamp']}id_/{item['original']}"
            body = b""
            actual_digest = ""
            try:
                response = session.get(replay, timeout=(8, timeout), stream=True)
                if response.status_code == 429:
                    item["fetch"] = {"status": "failed", "url": replay, "http_status": 429,
                                     "error": "Wayback returned HTTP 429; recovery paused to respect its rate limit"}
                    failures += 1
                    stopped = True
                    break
                response.raise_for_status()
                payload = bytearray()
                for chunk in response.iter_content(128 * 1024):
                    payload.extend(chunk)
                    if len(payload) > MAX_BYTES:
                        raise ValueError("Profile capture exceeded 25 MB safety limit")
                body = bytes(payload)
                soup = BeautifulSoup(body, "html.parser")
                if soup.html is None:
                    raise ValueError("Response did not contain an HTML document")
                actual_digest = cdx_sha1(body)
                if actual_digest != item["digest"]:
                    raise ValueError(f"CDX SHA-1 mismatch: {actual_digest} != {item['digest']}")
                sha256 = hashlib.sha256(body).hexdigest()
                raw_path = f"raw/{item.get('route_id', item['timestamp'])}.html"
                destination = directory / raw_path
                destination.write_bytes(body)
                title = soup.title.get_text(" ", strip=True) if soup.title else ""
                item.update(title=title, content_classification=(
                    "platform_error" if "javascript is not available" in soup.get_text(" ", strip=True).lower()
                    else "profile_content"),
                    fetch={"status": "recovered", "url": replay, "path": raw_path,
                           "sha256": sha256, "cdx_sha1": actual_digest,
                           "cdx_sha1_verified": True, "bytes": len(body),
                           "content_type": response.headers.get("Content-Type", ""),
                           "http_status": response.status_code})
                recovered += 1
            except ArchiveCooldown:
                raise
            except Exception as exc:
                error = f"{type(exc).__name__}: {exc}"
                if "CDX SHA-1 mismatch" in error and body:
                    raw_path = f"raw/unverified-{item.get('route_id', item['timestamp'])}.html"
                    destination = directory / raw_path
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(body)
                    item["fetch"] = {"status": "unverified", "url": replay, "path": raw_path,
                                     "sha256": hashlib.sha256(body).hexdigest(),
                                     "cdx_sha1": actual_digest, "cdx_sha1_verified": False,
                                     "bytes": len(body), "error": error}
                else:
                    item["fetch"] = {"status": "failed", "url": replay, "error": error}
                failures += 1
            manifest["last_recovery"] = {"attempted": attempted_total, "recovered": recovered,
                                          "failures": failures, "stopped_for_rate_limit": stopped}
            manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
            if delay:
                time.sleep(delay)
        verified_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        for item in captures:
            fetch = item.get("fetch", {})
            local = directory / str(fetch.get("path", "")) if fetch.get("path") else None
            if fetch.get("status") != "recovered" or not local or not local.is_file():
                continue
            actual = cdx_sha1(local.read_bytes())
            fetch["cdx_sha1"] = actual
            fetch["cdx_sha1_verified"] = actual == item.get("digest")
            fetch["cdx_verification_method"] = "local raw-byte SHA-1 compared with the base32 digest in the exact CDX row"
            fetch["cdx_verified_at"] = verified_at
            if actual != item.get("digest"):
                fetch["status"] = "unverified"
                fetch["error"] = f"CDX SHA-1 mismatch: {actual} != {item.get('digest')}"
        manifest["recovery_summary"] = {
            "indexed_mementos": len(captures),
            "distinct_cdx_digests": len({item["digest"] for item in captures}),
            "recovered_mementos": sum(item.get("fetch", {}).get("status") == "recovered" for item in captures),
            "verified_cdx_sha1": sum(item.get("fetch", {}).get("cdx_sha1_verified") is True for item in captures),
            "unrecovered_mementos": sum(item.get("fetch", {}).get("status") != "recovered" for item in captures),
            "cdx_sha1_mismatches": sum(item.get("fetch", {}).get("cdx_sha1_verified") is False for item in captures),
            "stopped_for_rate_limit": stopped,
        }
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
        reports[handle] = {"status": "indexed", **manifest["recovery_summary"],
                           "attempted_this_run": recovered + failures}
        if stopped:
            break
    return {"accounts": reports, "attempted_total": attempted_total}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--accounts", nargs="+", choices=sorted(ACCOUNTS),
                        default=["prometheusbrown", "bluescholars", "sabzi", "wongweezy", "canhsolo"])
    parser.add_argument("--max-files", type=int, default=100)
    parser.add_argument("--delay", type=float, default=0.3)
    parser.add_argument("--timeout", type=int, default=45)
    parser.add_argument("--retry-failed", action="store_true")
    args = parser.parse_args()
    print(json.dumps(recover(args.accounts, args.max_files, args.delay,
                             args.timeout, args.retry_failed), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
