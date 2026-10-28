#!/usr/bin/env python3
"""Search Archive-It public full text and preserve related dated captures.

Acquired HTML is kept in recovery-only storage; this workflow does not publish
third-party pages or media into the restored sites.
"""
from __future__ import annotations

from restore.cooldown import ArchiveCooldown, RecoverySession
import argparse
import hashlib
import html
import json
import re
import time
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import requests
from bs4 import BeautifulSoup

from restore.archive import validate_payload

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "recovery/archiveit"
SEARCH = "https://archive-it.org/explore/"
QUERIES = [
    "bluescholars.com", "prometheusbrown", "Sabzi Blue Scholars",
    "bluescholars myspace", "Blue Scholars Jamglue", "Blue Scholars Massline",
    "Blue Scholars 2007", "Blue Scholars 2009", "Blue Scholars 2011",
    "206proof.com", "masslinemedia.com", "Blue Scholars LiveJournal",
    "Blue Scholars forum", "Blue Scholars photos", "Blue Scholars video",
    "Blue Scholars Bumbershoot", "Blue Scholars Bayani", "Blue Scholars touring",
    "Sabzi DJ", "Prometheus Brown Blue Scholars",
]
MAX_BYTES = 25_000_000
CAPTURE_RE = re.compile(r"^https://wayback\.archive-it\.org/(\d+)/(\d{14})/(.+)$", re.I)


def _card_record(card, query: str) -> dict | None:
    title = card.select_one("h2 a[href]")
    if not title:
        return None
    replay = html.unescape(title.get("href", ""))
    match = CAPTURE_RE.match(replay)
    if not match:
        return None
    collection, timestamp, original = match.groups()
    original = html.unescape(original)
    source_field = card.select_one(".fulltext-url")
    source_url = source_field.select_one("a[href]").get_text(" ", strip=True) if source_field and source_field.select_one("a[href]") else original
    details = " ".join(card.stripped_strings)
    return {"query": query, "title": title.get_text(" ", strip=True), "original_url": html.unescape(source_url),
            "timestamp": timestamp, "collection_id": collection, "replay_url": replay,
            "result_text": details[:4000]}


def _relevant(record: dict) -> bool:
    direct = " ".join(str(record.get(k, "")) for k in ("title", "original_url")).casefold()
    if any(marker in direct for marker in (
            "blue scholar", "bluescholar", "prometheusbrown", "prometheus brown",
            "geologic", "jamglue", "twitpic.com/photos/prometheusbrown")):
        return True
    # Include a few otherwise generically titled source pages only when their
    # archived result snippet identifies the Blue Scholars media explicitly.
    snippet = str(record.get("result_text", "")).casefold()
    contextual = (
        "blue scholars film contest finalist", "blue scholars inkwell",
        "blue scholars \"slick watts\"", "pays homage to the seattle based hip-hop duo blue scholars",
        # Archive-It indexed a Common Market video as "a sequel to Blue
        # Scholars' 'Coffee and Snow'"; the title alone does not identify BS.
        "a sequel to blue scholars",
    )
    return any(marker in snippet for marker in contextual)


def _raw_replay(url: str) -> str:
    match = CAPTURE_RE.match(url)
    if not match:
        raise ValueError("Archive-It result URL is outside the expected capture format")
    collection, timestamp, original = match.groups()
    return f"https://wayback.archive-it.org/{collection}/{timestamp}id_/{original}"


def recover(limit: int = 100, delay: float = 0.8, pages: int = 3, start_page: int = 1,
            search_only: bool = False, retry_failed: bool = False,
            selected_queries: list[str] | None = None) -> dict:
    if limit < 1 or delay < 0 or pages < 1 or start_page < 1:
        raise ValueError("limit, pages and start_page must be positive and delay nonnegative")
    OUT.mkdir(parents=True, exist_ok=True)
    session = RecoverySession()
    session.headers["User-Agent"] = "BlueScholarsRestoration/0.1 (historical preservation)"
    manifest_path = OUT / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {
        "version": 1, "captures": {}}
    captures = manifest.setdefault("captures", {})
    attempts = manifest.setdefault("attempts", {})
    queries = selected_queries or QUERIES
    if selected_queries:
        slug = re.sub(r"[^a-z0-9]+", "-", "-".join(selected_queries).casefold()).strip("-")[:80]
        search_name = f"search-results-query-{slug}-pages-{start_page}-{start_page + pages - 1}.json"
    else:
        search_name = "search-results.json" if start_page == 1 else f"search-results-pages-{start_page}-{start_page + pages - 1}.json"
    search_path = OUT / search_name
    # Search requests are slow and independently repeatable. Keep each page as
    # it completes so an interrupted run resumes without discarding earlier
    # pages or issuing the same requests again.
    search_pages = json.loads(search_path.read_text(encoding="utf-8")) if search_path.exists() else []
    completed = {(item.get("query"), item.get("page")) for item in search_pages}
    found = {}
    for saved_page in search_pages:
        for item in saved_page.get("records", []):
            if _relevant(item):
                found.setdefault(item["replay_url"], item)
    report = {"archive": "Archive-It", "search_endpoint": SEARCH, "queries": [],
              "search_cards": 0, "relevant_capture_candidates": 0, "attempted": 0,
              "new_payloads": 0, "failures": [], "limitations": [
                  f"The public Explore page returns ranked results; this batch searches pages {start_page}-{start_page + pages - 1}, not a complete archive-wide export.",
                  "Only text/html capture bytes that pass structural validation are preserved by this script.",
                  "Raw third-party pages remain recovery-only pending rights review."]}
    for query in queries:
        for page in range(start_page, start_page + pages):
            if (query, page) in completed:
                saved = next((item for item in search_pages if item.get("query") == query and item.get("page") == page), None)
                if saved and not saved.get("records"):
                    break
                continue
            try:
                response = session.get(SEARCH, params={"q": query, "show": "ArchivedPages", "page": page}, timeout=(8, 25))
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")
                summary = soup.select_one(".fulltext-summary")
                cards = []
                for card in soup.select(".result-item.fulltext-hit"):
                    item = _card_record(card, query)
                    if item:
                        cards.append(item)
                        if _relevant(item):
                            found.setdefault(item["replay_url"], item)
                search_pages.append({"query": query, "page": page, "status": response.status_code,
                                     "summary": summary.get_text(" ", strip=True) if summary else "",
                                     "records": cards})
                search_path.write_text(json.dumps(search_pages, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                report["queries"].append({"query": query, "page": page, "status": response.status_code,
                                          "summary": summary.get_text(" ", strip=True) if summary else "",
                                          "records": len(cards)})
                report["search_cards"] += len(cards)
                if not cards:
                    break
            except ArchiveCooldown:
                raise
            except Exception as exc:
                report["queries"].append({"query": query, "page": page,
                                          "error": f"{type(exc).__name__}: {exc}"})
                break
            time.sleep(delay)

    report["relevant_capture_candidates"] = len(found)
    search_path.write_text(json.dumps(search_pages, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    def priority(pair):
        url, item = pair
        text = (item.get("title", "") + " " + item.get("original_url", "")).casefold()
        preferred = ("myspace.com/bluescholars", "twitter.com/bluescholars", "twitter.com/prometheusbrown",
                     "twitpic.com/photos/prometheusbrown", "prometheusbrown.tumblr.com",
                     "jamglue.com/contests/bluescholars", "kickstarter.com/projects/bluescholars",
                     "kexp.org", "mtv.com/music/artist/blue_scholars", "motherjones.com/radio/2006/08/geologic_bio")
        score = next((i for i, marker in enumerate(preferred) if marker in text), len(preferred))
        return score, item.get("timestamp", ""), url

    pending = [(url, item) for url, item in found.items()
               if not (url in captures and (ROOT / captures[url].get("raw_path", "")).is_file())
               and (retry_failed or url not in attempts or attempts[url].get("status") == "success")]
    rate_limited = False
    for source_url, candidate in ([] if search_only else sorted(pending, key=priority)[:limit]):
        if source_url in captures and (ROOT / captures[source_url].get("raw_path", "")).is_file():
            continue
        report["attempted"] += 1
        try:
            replay = _raw_replay(source_url)
            result = session.get(replay, timeout=(8, 35), stream=True)
            if result.status_code == 429:
                failure = {"replay_url": source_url, "title": candidate.get("title"),
                           "original_url": candidate.get("original_url"),
                           "error": "HTTP 429; stopped batch to respect Archive-It rate limit"}
                report["failures"].append(failure)
                attempts[source_url] = {"status": "failed", **failure}
                manifest["last_report"] = report
                manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                rate_limited = True
                break
            result.raise_for_status()
            content_type = result.headers.get("Content-Type", "").split(";", 1)[0].lower()
            if content_type not in ("text/html", "application/xhtml+xml"):
                raise ValueError(f"Unexpected capture content type: {content_type}")
            body = bytearray()
            for chunk in result.iter_content(128 * 1024):
                body.extend(chunk)
                if len(body) > MAX_BYTES:
                    raise ValueError("Capture exceeded 25 MB acquisition limit")
            payload = bytes(body)
            validate_payload(payload, "html")
            digest = hashlib.sha256(payload).hexdigest()
            path = f"recovery/archiveit/raw/{digest}.html"
            destination = ROOT / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            if not destination.exists():
                destination.write_bytes(payload)
            captures[source_url] = {**candidate, "sha256": digest, "bytes": len(payload),
                                     "raw_path": path, "kind": "html", "mime": content_type,
                                     "source_archive": "Archive-It", "raw_replay_url": replay,
                                     "review_required_before_publication": True}
            attempts[source_url] = {"status": "success", "sha256": digest, "raw_path": path}
            report["new_payloads"] += 1
        except ArchiveCooldown:
            raise
        except Exception as exc:
            failure = {"replay_url": source_url, "title": candidate.get("title"),
                       "original_url": candidate.get("original_url"),
                       "error": f"{type(exc).__name__}: {exc}"}
            report["failures"].append(failure)
            attempts[source_url] = {"status": "failed", **failure}
        time.sleep(delay)
        manifest["last_report"] = report
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    report["capture_records"] = len(captures)
    report["unique_payloads"] = len({item["sha256"] for item in captures.values()})
    report["rate_limited"] = rate_limited
    report["unattempted_candidates"] = max(0, len(pending) - report["attempted"])
    report["search_only"] = search_only
    manifest["last_report"] = report
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (OUT / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--delay", type=float, default=0.8)
    parser.add_argument("--pages", type=int, default=3, help="maximum Archive-It result pages per query")
    parser.add_argument("--start-page", type=int, default=1, help="first Archive-It result page (1-based)")
    parser.add_argument("--search-only", action="store_true", help="collect ranked results without requesting replay bodies")
    parser.add_argument("--retry-failed", action="store_true", help="retry URLs with a preserved replay failure")
    parser.add_argument("--query", dest="queries", action="append", help="search only this query (repeatable); defaults to the saved query set")
    args = parser.parse_args()
    print(json.dumps(recover(args.limit, args.delay, args.pages, args.start_page, args.search_only,
                             args.retry_failed, args.queries), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
