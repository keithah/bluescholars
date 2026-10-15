# Blue Scholars historical recovery report

**Updated:** October 15, 2026. **Scope:** separate copies of the 2007, 2009/WordPress, and Squarespace-era sites, with the May 29, 2021 homepage as the Squarespace visual reference.

## Evidence collected

### Internet Archive Wayback Machine

The saved domain CDX checkpoint is marked complete. Its acquisition report records 8,178 capture rows. The current resumable state contains 3,978 resource records and 7,631 capture rows attached to those records. The original run's domain scan has raw CDX batches preserved locally under `recovery/index/`; those generated working files are excluded from Git. A complete capture index describes available snapshots; it does not mean their response bodies have been downloaded.

Before the targeted exact image-host queries were added, the state exposed these latest-200-OK selections per URL: 373 resources in the 2007 date range, 799 in the 2009-to-pre-Squarespace range, and 193 in the Squarespace range. They are selection counts, not acquisition success counts. Use the `capture-era` command or the updated recovery workflow to fetch each selected dated response while preserving variants.

The existing selected homepage body is genuine HTML from `20210529010817`. Its reference photograph is separately identified at `20210529010844`, 27 seconds later. This is preserved as a resource-specific same-crawl dependency. The selected homepage CSS and the 2020 section pages are also present in the recovered source set. A Shop response captured in 2020 is a provider error; the raw bytes and provenance remain in recovery metadata but are not treated as shop content.

### Common Crawl

The initial local all-collection index sweep found 128 published index endpoints but reached only 6; 122 requests failed from that machine. Those six returned 380 unique domain responses, all acquired as original WARC records with collection, filename, offset, length, digest, and content hash recorded. Many are WordPress-era pages from the 2016/2017 crawls. This is useful independent evidence but is **not** full Common Crawl coverage.

Two additional collection queries were saved as reproducible JSONL seeds in `recovery/seeds/commoncrawl/`:

- `CC-MAIN-2009-2010.jsonl`: 19 valid archived site pages were fetched, including blog/article, bio, release, tour, and store routes from the early WordPress site.
- `CC-MAIN-2023-40.jsonl`: 5 page bodies were recovered from 16 relevant rows. Three `robots.txt` rows were rejected as non-HTML; the archived Shop response was rejected as a provider error. A captured blog/homepage response supplies a late Squarespace-era comparison point.

Common Crawl uses independent snapshots; identical capture hashes are deduplicated in storage but source rows remain documented. These captures do not replace Wayback captures from the requested editions.

### Arquivo.pt

The Arquivo.pt version-history query returned 12 root-page captures from 2017–2023. Three successful 200 responses (April 2018, July 2018, and October 2019) were retrieved as original HTML and retained as independent variants. The other statuses did not yield site-body bytes and are recorded as capture metadata, not as recovered pages. A broader follow-up now uses Arquivo.pt's documented domain CDX endpoint to enumerate indexed site URLs, preserving the raw index and downloading the latest 200 response per URL in each of the 2007, 2009, and 2013+ editions. That new scan is not yet run; no wider Arquivo.pt coverage is claimed here.

## Current saved source collection

`source/catalog.json` contains 3,268 inventory records. It points to 97 unique content-addressed original files in `source/raw/` (about 11.5 MB): 126 source records reference HTML bytes, 28 reference CSS bytes, and 3 reference image bytes. Several records intentionally share the same physical file by hash. The catalog also retains queued, failed, and review-needed findings; those are not usable content.

The current recovery checkpoint records 505 recovered and 6 review-needed resources, but only 511 raw records total (478 HTML and 33 CSS). There are no images in that checkpoint's newly downloaded raw set; the three images in the reviewed source collection came from the prior homepage recovery. Source records, alternate archive responses, and physical files are different counts, and are reported separately here.

## Current reconstruction and verification

The static builder produces a gateway and separate `/2007/`, `/2009/`, and `/2013/` editions. Candidate output is clearly separate from promoted sources. The current full candidate build contains 396 recovered pages, 641 source-gap placeholders, and 27 local generated assets. The offline link/resource checker passes at both `/` and `/bluescholars/`. Those checks establish internal consistency, not visual fidelity or completeness.

The automated suite has 96 passing tests. Pages is not enabled. `source/review.json` still has `visual_reviewed: false` and `publish_approved: false`.

## Resume commands

Locally, with working Internet Archive access:

```bash
python -m restore index --max-pages 20
python -m restore index-assets --max-assets 100 --max-pages 3
python -m restore recover --max-files 500 --retry-failed
python -m restore capture-era --era 2007 --max-files 2000
python -m restore capture-era --era 2009 --max-files 2000
python -m restore capture-era --era 2013 --max-files 2000
python -m restore commoncrawl --max-records 1800 --workers 4
python -m restore arquivo --history-url bluescholars.com
```

The manually dispatched GitHub Action is the current fallback for Wayback access. Resume its last saved `archive-recovery` artifact by passing its numeric run ID as `resume_run`; choose one `edition_era` per run. Download the resulting artifact into staging, inspect the checkpoint and raw files, then merge it without replacing newer local work. The workflow is retrieval-only and does not publish.
