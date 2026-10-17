#!/usr/bin/env python3
"""Inventory post links from already-recovered Squarespace blog archives.

This is an offline, resumable report update: it never contacts an archive and
never changes recovered source bytes. Re-running it deduplicates by normalized
source URL/capture/hash and by source-listing observation.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from urllib.parse import quote, urlsplit

from bs4 import BeautifulSoup

from restore.state import State
from restore.urls import TARGET, identity, original_url, route


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/recovery-report"


def cdx_url(url: str) -> str:
    return (
        "https://web.archive.org/cdx/search/cdx?url="
        + quote(url, safe="")
        + "&matchType=exact&output=json&fl=timestamp,original,statuscode,mimetype,digest,length"
        "&limit=500&showResumeKey=true"
    )


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    state = State(ROOT)
    manifest_path = REPORT / "recovery-manifest.json"
    manifest = read_json(manifest_path)
    records = manifest["records"]
    known_ids = {record["id"] for record in records}
    known_urls = {
        identity(record.get("original_url", ""))
        for record in records
        if record.get("kind") == "page" and record.get("original_url")
    }
    known_urls.discard("")
    record_by_url = {
        identity(record["original_url"]): record["id"]
        for record in records
        if record.get("kind") == "page" and record.get("original_url")
    }

    next_page = max(
        (int(record["id"][1:]) for record in records
         if record.get("id", "").startswith("P") and record["id"][1:].isdigit()),
        default=0,
    ) + 1
    next_blog = max(
        (int(item["id"][1:]) for item in manifest.get("blog_listing_observations", [])
         if item.get("id", "").startswith("B") and item["id"][1:].isdigit()),
        default=0,
    ) + 1

    # Select recovered listing captures only. The 2023 variant is retained in
    # P07 as a later alternative and is deliberately not mixed into this set.
    listing_captures: dict[tuple[str, str, str], tuple[str, dict, list]] = {}
    for key, record in state.data["resources"].items():
        if record.get("kind") != "html" or record.get("status") != "recovered":
            continue
        if not record.get("raw_path") or not record.get("actual_capture"):
            continue
        source_url = original_url(record.get("url", key))
        parts = urlsplit(source_url)
        if (parts.hostname or "").removeprefix("www.") != "bluescholars.com":
            continue
        if parts.path.rstrip("/") != "/blog" or record["actual_capture"] > TARGET:
            continue
        source_id = identity(source_url)
        # General pagination/listing pages already have source records and
        # capture histories. This pass focuses on previously unrecorded
        # tag/author archives.
        if source_id in known_urls:
            continue
        raw_path = ROOT / record["raw_path"]
        try:
            raw = raw_path.read_bytes()
        except OSError:
            continue
        if hashlib.sha256(raw).hexdigest() != record.get("sha256"):
            continue
        soup = BeautifulSoup(raw, "html.parser")
        entries = soup.select("article.hentry")
        if not entries:
            continue
        key = (source_id, record["actual_capture"], record["sha256"])
        listing_captures[key] = (source_url, record, entries)

    new_observations: list[dict] = []
    new_listing_records: list[dict] = []
    observed_routes: dict[str, dict] = {}
    capture_to_record: dict[tuple[str, str, str], str] = {}

    for key, (source_url, source_record, entries) in sorted(listing_captures.items()):
        capture = source_record["actual_capture"]
        raw = (ROOT / source_record["raw_path"]).read_bytes()
        page_id = f"P{next_page:02d}"
        next_page += 1
        capture_to_record[key] = page_id
        source_page = f"https://web.archive.org/web/{capture}/{source_url}"
        query_note = "Found in the completed local Wayback domain index; exact-URL CDX results were not separately requested."
        listing_record = {
            "id": page_id,
            "kind": "page",
            "label": urlsplit(source_url).path + ("?" + urlsplit(source_url).query if urlsplit(source_url).query else ""),
            "original_url": source_url,
            "archive_request_url": source_page,
            "request_timestamp": capture,
            "actual_capture_timestamp": capture,
            "status": "recovered_locally_from_individual_capture",
            "source_archive": source_record.get("source_archive") or "Internet Archive Wayback",
            "raw_candidate_url": f"https://web.archive.org/web/{capture}id_/{source_url}",
            "all_captures_url": "https://web.archive.org/web/*/" + source_url,
            "exact_cdx_query": cdx_url(source_url),
            "priority": "P2",
            "local_file": source_record["raw_path"],
            "sha256": source_record["sha256"],
            "bytes": len(raw),
            "rendered_candidate_path": "/2013" + route(source_url),
            "listing_entry_count": len(entries),
            "notes": (
                "Individually recovered Squarespace tag/author archive capture. "
                + query_note
                + " Listing entries are separately recorded as B observations; labels are finding aids, not asserted post titles."
            ),
        }
        records.append(listing_record)
        new_listing_records.append(listing_record)
        known_urls.add(identity(source_url))

        for order, item in enumerate(entries, 1):
            anchor = item.select_one("h1 a,h2 a,h3 a") or item.select_one("a[href]")
            if not anchor:
                continue
            permalink = original_url(anchor.get("href", ""), source_url)
            if not permalink:
                continue
            host = (urlsplit(permalink).hostname or "").removeprefix("www.")
            if host != "bluescholars.com":
                continue
            time_node = item.select_one("time")
            date = time_node.get("datetime", "") if time_node else ""
            title = anchor.get_text(" ", strip=True)
            slug = urlsplit(permalink).path.rstrip("/").rsplit("/", 1)[-1]
            finding = title or slug
            observed_routes.setdefault(identity(permalink), {
                "url": permalink,
                "source_url": source_url,
                "source_capture": capture,
                "slug": slug,
            })
            new_observations.append({
                "id": f"B{next_blog:03d}",
                "listing": 6,
                "order_in_listing": order,
                "publication_date_observed": date,
                "finding_aid_label": finding,
                "source_page": source_page,
                "source_page_record_id": page_id,
                "known_permalink_record": None,
                "observed_permalink_url": permalink,
                "note": "Observed in an individually recovered Squarespace tag/author archive. Label is a finding aid, not an asserted original title; post body provenance is recorded separately.",
            })
            next_blog += 1

    # Add one source record for each newly observed post route, choosing its
    # latest recovered body capture at or before the reference date.
    post_records: list[dict] = []
    for route_id, observed in sorted(observed_routes.items()):
        existing_id = record_by_url.get(route_id)
        if existing_id:
            observed["record_id"] = existing_id
            continue
        candidates = []
        for key, record in state.data["resources"].items():
            if record.get("kind") != "html" or record.get("status") != "recovered":
                continue
            if not record.get("raw_path") or identity(record.get("url", key)) != route_id:
                continue
            capture = record.get("actual_capture", "")
            if capture and capture <= TARGET:
                candidates.append(record)
        if not candidates:
            continue
        candidates.sort(key=lambda record: record.get("actual_capture", ""))
        body_record = candidates[-1]
        capture = body_record["actual_capture"]
        url = observed["url"]
        post_id = f"P{next_page:02d}"
        next_page += 1
        body_url = record_by_url.get(route_id)
        record = {
            "id": post_id,
            "kind": "page",
            "label": observed["slug"],
            "original_url": url,
            "archive_request_url": f"https://web.archive.org/web/{capture}/{url}",
            "request_timestamp": capture,
            "actual_capture_timestamp": capture,
            "status": "recovered_locally_from_existing_capture",
            "source_archive": body_record.get("source_archive") or "Internet Archive Wayback",
            "raw_candidate_url": f"https://web.archive.org/web/{capture}id_/{url}",
            "all_captures_url": "https://web.archive.org/web/*/" + url,
            "exact_cdx_query": cdx_url(url),
            "priority": "P1",
            "local_file": body_record["raw_path"],
            "sha256": body_record["sha256"],
            "bytes": body_record.get("bytes"),
            "rendered_candidate_path": "/2013" + route(url),
            "source_page": f"https://web.archive.org/web/{observed['source_capture']}/{observed['source_url']}",
            "notes": "Article body bytes were already recovered independently. The displayed label is the observed permalink slug, not an asserted original title.",
        }
        records.append(record)
        post_records.append(record)
        record_by_url[route_id] = post_id
        observed["record_id"] = post_id

    for observation in new_observations:
        observation["known_permalink_record"] = record_by_url.get(identity(observation["observed_permalink_url"]))

    current_observations = manifest.setdefault("blog_listing_observations", [])
    existing_pairs = {
        (item.get("source_page_record_id"), item.get("order_in_listing"), item.get("observed_permalink_url"))
        for item in current_observations
        if item.get("source_page_record_id")
    }
    current_observations.extend(
        item for item in new_observations
        if (item["source_page_record_id"], item["order_in_listing"], item["observed_permalink_url"]) not in existing_pairs
    )
    manifest["counts"]["page"] = sum(record.get("kind") == "page" for record in records)
    manifest["counts"]["total_records"] = len(records)
    if new_listing_records:
        manifest["important_notes"] = list(dict.fromkeys(manifest.get("important_notes", []) + [
            f"An offline pass over {len(new_listing_records)} individually recovered tag/author listing captures adds {len(new_observations)} source-linked entry observations. Newly observed post routes are recorded separately; no body is inferred from listing text."
        ]))
    write_json(manifest_path, manifest)

    fields = list(dict.fromkeys(key for record in records for key in record))
    with (REPORT / "recovery-manifest.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for record in records:
            writer.writerow({key: json.dumps(record.get(key), ensure_ascii=False)
                             if isinstance(record.get(key), (dict, list))
                             else "" if record.get(key) is None else record.get(key)
                             for key in fields})

    # Keep the CSV finding aid aligned with the machine-readable observations.
    checklist = REPORT / "blog-entry-checklist.csv"
    rows = []
    for item in manifest.get("blog_listing_observations", []):
        rows.append({
            "id": item["id"],
            "listing": str(item.get("listing", "")),
            "order_in_listing": str(item.get("order_in_listing", "")),
            "publication_date_observed": item.get("publication_date_observed", ""),
            "finding_aid_label": item.get("finding_aid_label", ""),
            "known_permalink_record": item.get("known_permalink_record") or "",
            "source_page": item.get("source_page", ""),
            "source_page_record_id": item.get("source_page_record_id", ""),
            "observed_permalink_url": item.get("observed_permalink_url", ""),
            "note": item.get("note", item.get("notes", "")),
        })
    checklist_fields = [
        "id", "listing", "order_in_listing", "publication_date_observed",
        "finding_aid_label", "source_page", "source_page_record_id",
        "known_permalink_record", "observed_permalink_url", "note",
    ]
    with checklist.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=checklist_fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    # Merge every newly catalogued page into both seed inventories by the
    # repository's full normalized URL identity; retain existing metadata.
    page_records = [record for record in records if record.get("kind") == "page"]
    for seed_path in (REPORT / "recovery-seeds-expanded.json", ROOT / "recovery/seeds/inventory.json"):
        seed = read_json(seed_path)
        pages = seed.setdefault("pages", [])
        page_identities = {identity(page.get("original_url", "")) for page in pages}
        for record in page_records:
            url = record.get("original_url", "")
            if not url or identity(url) in page_identities:
                continue
            parts = urlsplit(url)
            path = parts.path or "/"
            if parts.query:
                path += "?" + parts.query
            pages.append({
                "path": path,
                "original_url": url,
                "capture": record.get("actual_capture_timestamp") or record.get("request_timestamp") or "",
                "archive_url": record.get("archive_request_url") or "",
                "status": record.get("status", "observed_from_recovered_listing"),
                "notes": record.get("notes", ""),
            })
            page_identities.add(identity(url))
        write_json(seed_path, seed)

    print(json.dumps({
        "new_listing_captures": len(new_listing_records),
        "new_entry_observations": len(new_observations),
        "new_post_records": len(post_records),
        "total_records": len(records),
        "total_blog_observations": len(current_observations),
    }, indent=2))


if __name__ == "__main__":
    main()
