#!/usr/bin/env python3
"""Recover exact archived Twitter page-two URLs observed in saved profile HTML."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from restore.twitter import _cdx_sha1, _twitter_query_url

ACCOUNTS = ("prometheusbrown", "bluescholars", "sabzi", "wongweezy", "canhsolo")
CDX = "https://web.archive.org/cdx/search/cdx"


def recover(root: Path = ROOT, max_pages: int = 500, delay: float = 0.3,
            timeout: int = 45) -> dict:
    session = requests.Session()
    session.headers["User-Agent"] = "BlueScholarsRestoration/1.0 (historical preservation)"
    report = {}
    attempted_total = 0
    for account in ACCOUNTS:
        directory = root / f"recovery/twitter-{account}"
        manifest_path = directory / "manifest.json"
        if not manifest_path.exists():
            continue
        manifest = json.loads(manifest_path.read_text())
        observed = {}
        for capture in manifest.get("captures", []):
            fetch = capture.get("fetch", {})
            if fetch.get("status") != "recovered" or not fetch.get("path"):
                continue
            source = directory / fetch["path"]
            if not source.is_file():
                continue
            original = str(capture.get("original", ""))
            for link in BeautifulSoup(source.read_bytes(), "html.parser").select("a#more, a[rel~=next]"):
                href = str(link.get("href", ""))
                normalized = _twitter_query_url(href, original, account)
                if normalized:
                    observed.setdefault(normalized, []).append(str(capture.get("timestamp", "")))
        pages = manifest.get("pagination_pages", [])
        cdx_path = directory / "pagination-cdx.json"
        prior_cdx = json.loads(cdx_path.read_text()) if cdx_path.exists() else {"targets": []}
        cdx_by_target = {str(row.get("target_url")): row for row in prior_cdx.get("targets", [])}
        old = {(str(row.get("target_url")), str(row.get("timestamp")), str(row.get("digest"))): row for row in pages}
        indexed = []
        indexed_targets = []
        capture_limit = max_pages - attempted_total
        stopped = False
        for target, parents in sorted(observed.items()):
            fields = ["timestamp", "original", "statuscode", "mimetype", "digest", "length"]
            parts = urlsplit(target)
            query_urls = (target,
                          urlunsplit(("http", "twitter.com", parts.path, parts.query, "")),
                          urlunsplit(("http", "twitter.com:80", parts.path, parts.query, "")),
                          urlunsplit(("https", "mobile.twitter.com", parts.path, parts.query, "")))
            table = []
            selected_query = ""
            index_error = ""
            query_attempts = []
            for query_url in query_urls:
                query = {"url": query_url, "output": "json",
                         "filter": ["statuscode:200", "mimetype:text/html"],
                         "fl": "timestamp,original,statuscode,mimetype,digest,length"}
                try:
                    response = session.get(CDX, params=query, timeout=(8, timeout))
                    if response.status_code == 429:
                        stopped = True
                        index_error = "Wayback CDX returned HTTP 429; inventory paused"
                        query_attempts.append({"url": query_url, "http_status": 429,
                                               "result": "rate_limited"})
                        break
                    response.raise_for_status()
                    candidate = response.json()
                except Exception as exc:
                    index_error = f"{type(exc).__name__}: {exc}"
                    query_attempts.append({"url": query_url, "result": "request_failed",
                                           "error": index_error})
                    if delay:
                        time.sleep(delay)
                    continue
                if candidate and candidate[0] != fields:
                    index_error = "Unexpected CDX response columns"
                elif candidate and len(candidate) > 1:
                    query_attempts.append({"url": query_url, "http_status": response.status_code,
                                           "result": "rows", "rows": candidate[1:]})
                    table = candidate
                    selected_query = query_url
                    break
                query_attempts.append({"url": query_url, "http_status": response.status_code,
                                       "result": "no_rows"})
                if delay:
                    time.sleep(delay)
            if query_attempts:
                cdx_by_target[target] = {"target_url": target, "parent_captures": parents,
                                         "queries": query_attempts}
                cdx_path.write_text(json.dumps({"source": "Internet Archive CDX",
                    "fields": fields, "queried_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "targets": list(cdx_by_target.values())}, indent=2, ensure_ascii=False) + "\n")
            if stopped:
                indexed.extend(row for row in pages if row.get("target_url") == target)
                if not any(row.get("target_url") == target for row in indexed):
                    indexed_targets.append({"target_url": target, "parent_captures": parents,
                                            "status": "index_failed", "error": index_error})
                break
            if not table:
                indexed_targets.append({"target_url": target, "parent_captures": parents,
                                        "status": "not_indexed" if not index_error else "index_failed",
                                        **({"error": index_error} if index_error else {})})
                continue
            safe_id = hashlib.sha256(target.encode()).hexdigest()[:12]
            for row in table[1:]:
                if len(row) < 6:
                    continue
                stamp, original, status, mimetype, digest, length = row[:6]
                key = (target, stamp, digest)
                entry = old.get(key, {})
                route_id = f"{stamp}-{safe_id}"
                entry.update(target_url=target, parent_captures=parents, timestamp=stamp,
                             original=original, statuscode=status, mimetype=mimetype,
                             digest=digest, length=int(length) if str(length).isdigit() else None,
                             route_id=route_id, cdx_query_url=selected_query)
                fetch = entry.get("fetch", {})
                local = directory / str(fetch.get("path", "")) if fetch.get("path") else None
                if fetch.get("status") == "recovered" and local and local.is_file():
                    indexed.append(entry)
                    continue
                if attempted_total >= max_pages:
                    indexed.append(entry)
                    continue
                attempted_total += 1
                replay = f"https://web.archive.org/web/{stamp}id_/{original}"
                body = b""
                try:
                    page = session.get(replay, timeout=(8, timeout))
                    if page.status_code == 429:
                        entry["fetch"] = {"status": "failed", "url": replay, "http_status": 429,
                                          "error": "Wayback returned HTTP 429; recovery paused"}
                        stopped = True
                        indexed.append(entry)
                        break
                    page.raise_for_status()
                    body = page.content
                    soup = BeautifulSoup(body, "html.parser")
                    if soup.html is None:
                        raise ValueError("Response did not contain an HTML document")
                    actual = _cdx_sha1(body)
                    if actual != digest:
                        raise ValueError(f"CDX SHA-1 mismatch: {actual} != {digest}")
                    relative = f"raw/pagination/{route_id}.html"
                    destination = directory / relative
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(body)
                    entry["title"] = soup.title.get_text(" ", strip=True) if soup.title else ""
                    entry["fetch"] = {"status": "recovered", "url": replay, "path": relative,
                                      "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest(),
                                      "cdx_sha1": actual, "cdx_sha1_verified": True,
                                      "content_type": page.headers.get("Content-Type", ""),
                                      "http_status": page.status_code}
                except Exception as exc:
                    entry["fetch"] = {"status": "unverified" if body else "failed", "url": replay,
                                      "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest() if body else "",
                                      "cdx_sha1": _cdx_sha1(body) if body else "",
                                      "cdx_sha1_verified": False if body else None,
                                      "error": f"{type(exc).__name__}: {exc}"}
                    if body:
                        relative = f"raw/unverified-pagination-{route_id}.html"
                        destination = directory / relative
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        destination.write_bytes(body)
                        entry["fetch"]["path"] = relative
                indexed.append(entry)
                if delay and not stopped:
                    time.sleep(delay)
            if stopped:
                break
        # Preserve every previously recovered memento if this run encountered a
        # transient CDX limit before reaching its target.
        present = {(row.get("target_url"), row.get("timestamp"), row.get("digest")) for row in indexed}
        for row in pages:
            key = (row.get("target_url"), row.get("timestamp"), row.get("digest"))
            if key not in present and row.get("fetch", {}).get("status") in ("recovered", "unverified"):
                indexed.append(row)
        manifest["pagination_pages"] = indexed
        manifest["pagination_targets"] = indexed_targets
        manifest["pagination_inventory"] = {
            "method": "Exact query URL extracted from a checksum-verified profile capture, indexed and fetched via Internet Archive CDX",
            "observed_targets": len(observed), "indexed_mementos": sum(bool(row.get("timestamp")) for row in indexed),
            "verified_pages": sum(row.get("fetch", {}).get("cdx_sha1_verified") is True for row in indexed),
            "not_indexed_targets": sum(row.get("status") == "not_indexed" for row in indexed_targets),
            "queried_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "stopped_for_rate_limit": stopped,
        }
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
        report[account] = manifest["pagination_inventory"]
        if stopped:
            break
    return {"accounts": report, "attempted": attempted_total}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--max-pages", type=int, default=500)
    parser.add_argument("--delay", type=float, default=1.5)
    parser.add_argument("--timeout", type=int, default=45)
    args = parser.parse_args()
    if args.max_pages < 1 or args.delay < 0 or args.timeout < 1:
        parser.error("max-pages and timeout must be positive; delay must be nonnegative")
    print(json.dumps(recover(args.root, args.max_pages, args.delay, args.timeout), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
