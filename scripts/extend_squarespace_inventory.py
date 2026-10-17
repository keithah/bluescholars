#!/usr/bin/env python3
"""Merge an individually inspected older Squarespace listing into source inventories."""
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/recovery-report"
SOURCE_PAGE = "https://web.archive.org/web/20160611143343/http://bluescholars.com/blog?offset=1358016466000"
RAW = "recovery/raw/8dc84128b2368456b9bbe1f8d107acbee3a2f89e8511353ea1bbaff323f27fda.html"
SHA = "8dc84128b2368456b9bbe1f8d107acbee3a2f89e8511353ea1bbaff323f27fda"
NOTE = "Observed in recovered 2016 Squarespace listing HTML; label is a finding aid, not an asserted original title. The article slug is observed in the listing link; article body recovery is tracked independently."
ENTRIES = [
    ("2013-01-12", "Los Angeles tour photos", "/blog/brownouts-la-crane-thig-hollis-los-angeles"),
    ("2013-01-11", "Los Angeles tour photo reblog", "/blog/brownouts-la-crane-thig-hollis-los-angeles"),
    ("2013-01-08", "TourAllday footage", "/blog/12-minutes-of-random-ass-footage-from-tourallday"),
    ("2012-12-11", "Santa Cruz tour photo", "/blog/tigloandcole-jackwnewton-tourallday-santa"),
    ("2012-12-07", "Hollis family photo", "/blog/photo-by-holliss-mom"),
    ("2012-12-07", "Sabzi portrait", "/blog/jackwnewton-sabzi-of-the-blue-scholars-by"),
    ("2012-12-07", "Wild Buffalo performance photo", "/blog/pamjane-blue-scholars-the-wild-buffalo"),
    ("2012-12-07", "Geo portrait", "/blog/jackwnewton-geo-of-the-blue-scholars-by-jack"),
    ("2012-12-07", "Geo pulled on stage", "/blog/youh0esdown-got-pulled-up-on-stage-last-night"),
    ("2012-12-07", "Townfolk at Santa Cruz", "/blog/thignat-townfolk-at-santa-cruz-main-beach"),
    ("2012-12-01", "Unmixed Blue Scholars track request", "/blog/bluescholars-new-unmixed-unmastered-track"),
    ("2012-11-30", "Unmixed track master request", "/blog/new-unmixed-unmastered-track-anybody-wanna-master"),
    ("2012-11-28", "Sabzi at QC Cleaners", "/blog/jordanloveskats-shot-from-today-2-sabzi-in"),
    ("2012-11-27", "Anna Karina film text", "/blog/bluescholars-anna-karina-is-distinct-for"),
    ("2012-11-27", "Anna Karina film text reblog", "/blog/anna-karina-is-distinct-for-making-eye-contact"),
    ("2012-11-27", "Anna Karina music video notice", "/blog/bluescholars-anna-karina-music-video-directed"),
    ("2012-11-26", "Anna Karina video reminder", "/blog/bluescholars-anna-karina-music-video-directed"),
    ("2012-11-26", "Anna Karina video promotion", "/blog/anna-karina-music-video-directed-by-matt-jay"),
    ("2012-11-13", "TownAllday tour announcement", "/blog/bluescholars-townallday-tour-tickets-on-sale"),
    ("2012-11-13", "Sabzi guest in local video", "/blog/jordanloveskats-if-you-do-only-one-thing-today"),
]

def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")

def main() -> None:
    listing_rows = []
    for i, (date, label, permalink) in enumerate(ENTRIES, 41):
        row = {
            "id": f"B{i:02d}", "listing": 3, "order_in_listing": i - 40,
            "publication_date_observed": date, "finding_aid_label": label,
            "source_page": SOURCE_PAGE, "known_permalink_record": None,
            "observed_permalink_url": "http://bluescholars.com" + permalink,
            "note": NOTE,
        }
        listing_rows.append(row)

    # Each distinct article route maps to its own source record; duplicate listing
    # rows intentionally point to the same record.
    manifest_path = REPORT / "recovery-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    existing_by_url = {r.get("original_url"): r.get("id") for r in manifest["records"] if r.get("original_url")}
    for row in listing_rows:
        row["known_permalink_record"] = existing_by_url.get(row["observed_permalink_url"])

    csv_path = REPORT / "blog-entry-checklist.csv"
    with csv_path.open(newline="", encoding="utf-8") as f:
        old_rows = list(csv.DictReader(f))
        fields = list(old_rows[0])
    if "observed_permalink_url" not in fields:
        fields.append("observed_permalink_url")
    for row in old_rows:
        row.setdefault("observed_permalink_url", "")
    old_rows = [r for r in old_rows if not r["id"].startswith("B4") or r["id"] <= "B40"]
    by_id = {r["id"]: r for r in old_rows}
    by_id.update({r["id"]: r for r in listing_rows})
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader(); w.writerows(sorted(by_id.values(), key=lambda r: r["id"]))

    p09 = next(r for r in manifest["records"] if r["id"] == "P09")
    p09.update({
        "status": "alternate_capture_recovered; requested_capture_provider_error",
        "actual_capture_timestamp": "20160611143343",
        "alternate_capture_day": "2016-06-11",
        "alternate_archive_request_url": SOURCE_PAGE,
        "local_file": RAW,
        "sha256": SHA,
        "bytes": (ROOT / RAW).stat().st_size,
        "notes": "The requested 2019 replay was individually inspected and is a Wayback service-provider error. An older capture identified by the replay toolbar was retrieved and inspected: the 2016-06-11 Squarespace listing contains 20 article.hentry items from 2013-01-12 through 2012-11-13. It is the recovered fallback for listing content; the 2019 capture remains an error and is not treated as recovered. Article bodies are separate inventory records.",
    })
    p09.pop("resolved_replay_url", None)
    manifest["blog_listing_observations"] = [r for r in manifest["blog_listing_observations"] if r["id"] < "B41"] + listing_rows
    note = "An individually inspected 2016-06-11 Squarespace listing capture adds B41-B60; the 2019 replay for the same URL is a provider error. Finding-aid labels are not original titles, and article bodies remain separately tracked."
    manifest["important_notes"] = list(dict.fromkeys(manifest["important_notes"]))
    if note not in manifest["important_notes"]:
        manifest["important_notes"].append(note)
    # Keep the CSV mirror of the source-record inventory synchronized.
    manifest_csv = REPORT / "recovery-manifest.csv"
    with manifest_csv.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f)); fields = list(rows[0])
    mirror = next(r for r in rows if r["id"] == "P09")
    for key, value in p09.items():
        if key in mirror:
            mirror[key] = json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else ("" if value is None else str(value))
    with manifest_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n"); w.writeheader(); w.writerows(rows)

    query_path = REPORT / "capture-search-queries.csv"
    with query_path.open(newline="", encoding="utf-8") as f:
        queries = list(csv.DictReader(f)); fields = list(queries[0])
    for q in queries:
        if q["id"] == "Q03":
            q["query_result"] = "Exact CDX results were not obtained as a standalone response. Replay toolbar showed 2016-06-11; retrieved and inspected capture 20160611143343 (raw SHA-256 " + SHA + "). The requested 20190719224039 replay is a provider error."
        elif q["id"] == "Q04":
            q["query_result"] = "Recovered 20160611143343 listing capture (124320 bytes; SHA-256 " + SHA + "). It contains 20 article.hentry entries, Jan 12-Nov 13 2012/2013. This is a retrieved capture, not an independently obtained CDX response."
    with query_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n"); w.writeheader(); w.writerows(queries)

    # Preserve each observed third-listing route as its own recoverable source record.
    manifest["records"] = [r for r in manifest["records"] if r.get("status") != "queued_for_individual_capture_review"]
    known = {r["original_url"] for r in manifest["records"] if r.get("original_url")}
    candidate_status = json.loads((ROOT / "_candidate/archive-status/report.json").read_text())
    recovered_pages = {r["canonical_url"]: r for r in candidate_status["pages"] if r.get("canonical_url")}
    for n, (date, label, permalink) in enumerate(ENTRIES, 41):
        original = "http://bluescholars.com" + permalink
        if original in known:
            continue
        rid = f"P{15 + n - 41:02d}"
        page = recovered_pages.get(original, {})
        captured = page.get("actual_capture")
        archive = page.get("source_archive")
        if page.get("status") == "recovered":
            state = "recovered_locally_from_individual_capture"
            archive_url = ("https://web.archive.org/web/" + str(captured) + "/" + original if archive == "Internet Archive Wayback" else "")
        else:
            state = "queued_for_individual_capture_review"
            archive_url = "https://web.archive.org/web/20160611143343/" + original
        manifest["records"].append({
            "id": rid, "kind": "page", "label": permalink,
            "original_url": original,
            "archive_request_url": archive_url,
            "request_timestamp": captured or "20160611143343",
            "actual_capture_timestamp": captured,
            "status": state,
            "source_archive": archive,
            "rendered_candidate_path": page.get("path"),
            "source_page": SOURCE_PAGE,
            "raw_candidate_url": ("https://web.archive.org/web/" + str(captured) + "id_/" + original if archive == "Internet Archive Wayback" and captured else "https://web.archive.org/web/20160611143343id_/" + original if not captured else None),
            "all_captures_url": "https://web.archive.org/web/*/" + original,
            "exact_cdx_query": "https://web.archive.org/cdx/search/cdx?url=" + __import__("urllib.parse", fromlist=["quote"]).quote(original, safe="") + "&matchType=exact&output=json&fl=timestamp,original,statuscode,mimetype,digest,length&limit=500&showResumeKey=true",
            "priority": "P1", "notes": f"{date}; observed permalink link in listing entry B{n:02d}. {label} is a research aid, not an asserted original title. " + (f"Locally recovered from {archive} capture {captured}." if captured else "No matching recovered candidate page was indexed; inspect captures individually."),
            "local_file": None,
        })
        known.add(original)
    record_ids_by_url = {r.get("original_url"): r.get("id") for r in manifest["records"] if r.get("original_url")}
    for row in manifest["blog_listing_observations"]:
        if row.get("observed_permalink_url"):
            row["known_permalink_record"] = record_ids_by_url.get(row["observed_permalink_url"])
    manifest["blog_listing_observations"] = [r for r in manifest["blog_listing_observations"] if r["id"] < "B41"] + listing_rows
    manifest["counts"]["page"] = sum(r.get("kind") == "page" for r in manifest["records"])
    manifest["counts"]["total_records"] = len(manifest["records"])
    write_json(manifest_path, manifest)

    # Recreate the source-record CSV including newly queued post routes and full P09 provenance.
    fields = list(dict.fromkeys(k for record in manifest["records"] for k in record))
    with manifest_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        for record in manifest["records"]:
            w.writerow({k: json.dumps(record.get(k), ensure_ascii=False) if isinstance(record.get(k), (dict, list)) else ("" if record.get(k) is None else record.get(k)) for k in fields})

    # Expanded seed mirror provides provenance to later recovery batches.
    seeds_path = REPORT / "recovery-seeds-expanded.json"
    seeds = json.loads(seeds_path.read_text())
    seeds["important_notes"] = list(dict.fromkeys(seeds.get("important_notes", [])))
    seeds["blog_listing_observations"] = [r for r in seeds.get("blog_listing_observations", []) if r.get("id", "") < "B41"] + listing_rows
    for record in seeds.get("records", []):
        if record.get("id") == "P09":
            record.update({k: p09[k] for k in ("status", "actual_capture_timestamp", "alternate_archive_request_url", "local_file", "sha256", "bytes", "notes")})
    seed_records = {r.get("id") for r in seeds.get("records", [])}
    seeds.setdefault("records", []).extend(r for r in manifest["records"] if r.get("id", "").startswith("P") and int(r["id"][1:]) >= 15 and r["id"] not in seed_records)
    seed_note = "B41-B60 were inspected in the recovered 2016-06-11 Squarespace listing. Individual post-body recovery status remains separate."
    if seed_note not in seeds.setdefault("important_notes", []):
        seeds["important_notes"].append(seed_note)
    seeds["stage"] = "Expanded report seed inventory; the zero-download value below describes the original handoff baseline."
    seeds["current_recovery_state"] = {
        "updated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "resource_urls": 8952,
        "indexed_capture_records": 9271,
        "unique_downloaded_files": 1972,
        "downloaded_bytes": 108454143,
        "candidate_pages_recovered": 924,
        "candidate_pages_placeholder": 1851,
        "source_checkpoint_artifact": "38975520061",
        "additional_local_capture": {"timestamp": "20160611143343", "url": "http://bluescholars.com/blog?offset=1358016466000", "sha256": SHA},
    }
    write_json(seeds_path, seeds)

    # Checkpoint and gap report summaries count observations, not recovered bodies.
    cp_path = REPORT / "current-checkpoint.json"
    cp = json.loads(cp_path.read_text())
    cp["updated_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    cp["older_edition_browser_observations"]["2013_squarespace"] = "An individually inspected 2016-06-11 Squarespace blog listing adds 20 observed entries (B41-B60); its 2019 replay is a provider error. Article body statuses are tracked independently."
    cp["squarespace_older_listing"] = {
        "source_capture": "20160611143343", "source_page": SOURCE_PAGE,
        "raw_file": RAW, "bytes": p09["bytes"], "sha256": SHA,
        "observed_entries": 20, "inventory_range": "B41-B60",
        "requested_2019_capture": "provider error", "article_bodies_inferred_recovered": False,
    }
    cp["next_queued_batch"]["status"] = cp["next_queued_batch"].get("status", "in_progress")
    write_json(cp_path, cp)

    gap_path = REPORT / "GAP_REPORT.json"
    gap = json.loads(gap_path.read_text())
    gap["updated_at"] = "2026-10-17T00:30:00Z"
    gap["squarespace_listing_coverage"] = {
        "observed_listing_entries": 60, "listing_captures": ["20201109000819", "20200220154840", "20160611143343"],
        "newly_added_entries": 20, "new_entries_ids": "B41-B60",
        "older_listing_raw_sha256": SHA,
        "post_bodies": "Not implied by listing observations; inventory/recovery statuses remain independent.",
    }
    write_json(gap_path, gap)

    for md in [REPORT / "GAP_REPORT.md", REPORT / "RECOVERY_REPORT.md"]:
        content = md.read_text()
        paragraph = ("\nAn older Squarespace listing was also retrieved from the June 11, 2016 capture after individually inspecting the 2019 replay (a Wayback provider error). The 2016 HTML contains 20 entries from January 12, 2013 through November 13, 2012; these are inventoried as B41–B60 with observed permalink slugs. Those entries point to 18 distinct article routes, and all 18 have locally recovered pages from individual 2017–2019 Wayback or 2017 Common Crawl captures; the listing itself is not misrepresented as containing the article bodies. Raw listing source: `" + RAW + "` (SHA-256 `" + SHA + "`). The rebuilt page is `/2013/blog/page/3/`.\n")
        if "B41–B60" not in content:
            content += paragraph
        md.write_text(content)

if __name__ == "__main__":
    main()
