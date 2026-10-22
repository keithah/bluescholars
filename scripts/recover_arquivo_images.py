#!/usr/bin/env python3
"""Search Arquivo.pt's independent image index for Blue Scholars source media.

The image results are leads, not publication approval. Every downloaded asset
is kept in the recovery-only area with its image memento and source-page
provenance for separate review.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import time
from pathlib import Path
from urllib.parse import urlsplit

import requests

from restore.archive import validate_payload

API = "https://arquivo.pt/imagesearch"
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "recovery/arquivo-images"
QUERIES = ('"Blue Scholars" band', 'Geologic Blue Scholars', 'Sabzi Blue Scholars',
           'myspace.com/bluescholars', 'Blue Scholars Myspace profile',
           'prometheusbrown Twitpic', 'Blue Scholars band Seattle photo')
MAX_BYTES = 25_000_000


def _text(item: dict, *keys: str) -> str:
    return " ".join(str(item.get(key) or "") for key in keys).casefold()


def is_relevant(item: dict) -> bool:
    """Keep band-specific page/image leads and exclude similarly named projects."""
    text = _text(item, "pageTitle", "pageURL", "imgSrc", "imgAlt", "imgTitle", "imgCaption")
    if "blue scholars initiative" in text or "blue-scholars-initative" in text:
        return False
    # Do not treat the common word "geologic" alone as a band reference.
    # It produced many unrelated geology/tourism images in later result pages.
    markers = ("blue scholars", "blue_scholars", "bluescholars", "prometheusbrown",
               "prometheus brown", "sabzi of blue scholars")
    return any(marker in text for marker in markers)


def _suffix(body: bytes) -> str:
    if body.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if body.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if body.startswith((b"GIF87a", b"GIF89a")):
        return ".gif"
    if body.startswith(b"RIFF") and body[8:12] == b"WEBP":
        return ".webp"
    raise ValueError("Arquivo.pt response is not a recognized raster image")


def recover(limit: int = 100, delay: float = 0.5, pages: int = 3, start_page: int = 1) -> dict:
    if limit < 1 or delay < 0 or pages < 1 or start_page < 1:
        raise ValueError("limit, pages and start_page must be positive and delay nonnegative")
    OUT.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers["User-Agent"] = "BlueScholarsRestoration/0.1 (historical preservation)"
    responses = []
    leads: dict[str, dict] = {}
    report = {"archive": "Arquivo.pt Image Search and Wayback", "query_endpoint": API,
              "queries": [], "leads": 0, "download_attempted": 0, "recovered": 0,
              "failures": [], "limitations": [
                  f"Image Search returns ranked results; this batch requests pages {start_page}-{start_page + pages - 1} for selected queries, not the full corpus.",
                  "Search relevance and archived bytes do not establish that an image depicts Blue Scholars or can be republished."]}
    for query in QUERIES:
        for page in range(start_page, start_page + pages):
            offset = (page - 1) * 50
            try:
                response = session.get(API, params={"q": query, "maxItems": 50, "offset": offset,
                                                    "prettyPrint": "true", "from": "20070101000000",
                                                    "to": "20261231235959"}, timeout=45)
                response.raise_for_status()
                payload = response.json()
                items = payload.get("responseItems", [])
                responses.append({"query": query, "totalItems": payload.get("totalItems"),
                                  "numberOfResponseItems": payload.get("numberOfResponseItems"),
                                  "offset": payload.get("offset", offset), "items": items})
                report["queries"].append({"query": query, "totalItems": payload.get("totalItems"),
                                          "returned": len(items), "offset": payload.get("offset", offset)})
                for item in items:
                    link = str(item.get("imgLinkToArchive") or "")
                    if is_relevant(item) and link:
                        leads.setdefault(link, {**item, "matched_queries": []})["matched_queries"].append(query)
                if len(items) < 50:
                    break
            except Exception as exc:
                report["queries"].append({"query": query, "offset": offset,
                                          "error": f"{type(exc).__name__}: {exc}"})
                break
            time.sleep(delay)

    result_name = "query-results.json" if start_page == 1 else f"query-results-pages-{start_page}-{start_page + pages - 1}.json"
    (OUT / result_name).write_text(json.dumps(responses, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    old_path = OUT / "manifest.json"
    old = json.loads(old_path.read_text(encoding="utf-8")) if old_path.exists() else {"version": 1, "assets": {}}
    assets = old.setdefault("assets", {})
    for link, lead in leads.items():
        lead["matched_queries"] = sorted(set(lead["matched_queries"]))
        if urlsplit(link).scheme != "https" or urlsplit(link).hostname not in ("arquivo.pt", "www.arquivo.pt"):
            report["failures"].append({"archive_url": link, "error": "Rejected archive URL outside arquivo.pt"})
            continue
        key = link
        if key in assets and (ROOT / assets[key].get("raw_path", "")).is_file():
            continue
        if report["download_attempted"] >= limit:
            break
        report["download_attempted"] += 1
        try:
            result = session.get(link, timeout=45, stream=True)
            result.raise_for_status()
            content_type = result.headers.get("Content-Type", "").split(";", 1)[0].lower()
            if not content_type.startswith("image/"):
                raise ValueError(f"Unexpected content type: {content_type}")
            body = bytearray()
            for chunk in result.iter_content(128 * 1024):
                body.extend(chunk)
                if len(body) > MAX_BYTES:
                    raise ValueError("Image exceeded 25 MB acquisition limit")
            raw = bytes(body)
            validate_payload(raw, "image")
            suffix = _suffix(raw)
            digest = hashlib.sha256(raw).hexdigest()
            relative = f"recovery/arquivo-images/raw/{digest}{suffix}"
            destination = ROOT / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            if not destination.exists():
                destination.write_bytes(raw)
            assets[key] = {"sha256": digest, "bytes": len(raw), "raw_path": relative,
                           "kind": "image", "mime": content_type,
                           "source_archive": "Arquivo.pt Image Search and Wayback",
                           "archive_url": link, "image_timestamp": str(lead.get("imgTstamp", "")),
                           "source_image_url": lead.get("imgSrc"),
                           "source_page_url": lead.get("pageURL"),
                           "source_page_timestamp": str(lead.get("pageTstamp", "")),
                           "source_page_title": lead.get("pageTitle"),
                           "image_title": lead.get("imgTitle"), "image_alt": lead.get("imgAlt"),
                           "image_caption": lead.get("imgCaption"),
                           "image_dimensions": [lead.get("imgWidth"), lead.get("imgHeight")],
                           "matched_queries": lead["matched_queries"],
                           "review_required_before_publication": True}
            report["recovered"] += 1
        except Exception as exc:
            report["failures"].append({"archive_url": link, "source_image_url": lead.get("imgSrc"),
                                       "error": f"{type(exc).__name__}: {exc}"})
        time.sleep(delay)
    report["leads"] = len(leads)
    report["assets"] = len(assets)
    old["last_report"] = report
    old["assets"] = assets
    old_path.write_text(json.dumps(old, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    report_path = OUT / "report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=100, help="maximum number of archive image downloads")
    parser.add_argument("--delay", type=float, default=0.5, help="delay between archive requests")
    parser.add_argument("--pages", type=int, default=3, help="maximum 50-result pages per query")
    parser.add_argument("--start-page", type=int, default=1, help="first 50-result page (1-based)")
    args = parser.parse_args()
    print(json.dumps(recover(args.limit, args.delay, args.pages, args.start_page), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
