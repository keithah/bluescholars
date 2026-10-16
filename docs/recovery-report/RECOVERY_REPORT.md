# Blue Scholars historical recovery report

**Updated:** October 16, 2026. **Scope:** separate copies of the 2007, 2009/WordPress, and Squarespace-era sites, with the May 29, 2021 homepage as the Squarespace visual reference.

## Evidence collected

### Internet Archive Wayback Machine

The saved domain CDX checkpoint is marked complete. Its acquisition report records 8,178 capture rows. The saved run initially contained 3,978 resource records. After merging a partial 2007 batch artifact, the current local checkpoint contains 4,259 resource records and 8,319 attached capture rows. The saved pre-merge acquisition report counted 8,178 rows. The original run's domain scan has raw CDX batches preserved locally under `recovery/index/`; those generated working files are excluded from Git. A complete capture index describes available snapshots; it does not mean their response bodies have been downloaded.

Before the targeted exact image-host queries were added, the state exposed these latest-200-OK selections per URL: 373 resources in the 2007 date range, 799 in the 2009-to-pre-Squarespace range, and 193 in the Squarespace range. They are selection counts, not acquisition success counts. Use the `capture-era` command or the updated recovery workflow to fetch each selected dated response while preserving variants.

The existing selected homepage body is genuine HTML from `20210529010817`. Its reference photograph is separately identified at `20210529010844`, 27 seconds later. This is preserved as a resource-specific same-crawl dependency. The selected homepage CSS and the 2020 section pages are also present in the recovered source set. A Shop response captured in 2020 is a provider error; the raw bytes and provenance remain in recovery metadata but are not treated as shop content.

### Common Crawl

The initial local all-collection index sweep found 128 published index endpoints but reached only 6; 122 requests failed from that machine. Those six returned 380 unique domain responses, all acquired as original WARC records with collection, filename, offset, length, digest, and content hash recorded. Many are WordPress-era pages from the 2016/2017 crawls. This is useful independent evidence but is **not** full Common Crawl coverage.

Two additional collection queries were saved as reproducible JSONL seeds in `recovery/seeds/commoncrawl/`:

- `CC-MAIN-2009-2010.jsonl`: 19 valid archived site pages were fetched, including blog/article, bio, release, tour, and store routes from the early WordPress site.
- `CC-MAIN-2023-40.jsonl`: 5 page bodies were recovered from 16 relevant rows. Three `robots.txt` rows were rejected as non-HTML; the archived Shop response was rejected as a provider error. A captured blog/homepage response supplies a late Squarespace-era comparison point.

Common Crawl uses independent snapshots; identical capture hashes are deduplicated in storage but source rows remain documented. These captures do not replace Wayback captures from the requested editions.

### Arquivo.pt

The Arquivo.pt version-history query returned 12 root-page captures from 2017–2023. Three successful 200 responses (April 2018, July 2018, and October 2019) were retrieved as original HTML and retained as independent variants. The other statuses did not yield site-body bytes and are recorded as capture metadata, not as recovered pages. A broader follow-up now uses Arquivo.pt's documented domain CDX endpoint to enumerate indexed site URLs, preserving the raw index and downloading the latest 200 response per URL in each of the 2007, 2009, and 2013+ editions. The full-domain Arquivo.pt scan is still unverified against live results: the latest 2007 workflow hit its 90-minute job limit during Wayback recovery, before reaching the Arquivo.pt step. The corrected 2007 workflow `38834520393` is in progress; its Wayback dependency-recovery step began at 2026-10-16 01:20 UTC. Arquivo.pt has not yet been reached in this run.

### Other archive checks

The Library of Congress documents wildcard capture browsing for exact URLs; a focused catalog API query for `bluescholars.com` timed out without a response, so no conclusion is drawn from that service. The documented Archive-It global CDX query for the exact domain returned HTTP 403. Its official guide says `/all` is temporarily blocked; collection-specific queries require a collection ID. Focused web searches for Archive-It, LoC, and other public indexes did not surface a specific independent site copy. A previous Archive.ph request was rate-limited (HTTP 429), and the previous Memento Time Travel query could not be accessed through the research reader. These are access/search limitations, not evidence that those archives contain no material. The Library of Congress documents its search interface at [Tips on Searching the Web Archive](https://www.loc.gov/programs/web-archiving/for-researchers/searching-the-web-archive/) and the [Archive-It CDX/C API guide](https://support.archive-it.org/hc/en-us/articles/115001790023-Access-Archive-It-s-Wayback-index-with-the-CDX-C-API).

## Current saved source collection

`source/catalog.json` contains 3,268 inventory records. It points to 97 unique content-addressed original files in `source/raw/` (about 11.5 MB): 126 source records reference HTML bytes, 28 reference CSS bytes, and 3 reference image bytes. Several records intentionally share the same physical file by hash. The catalog also retains queued, failed, and review-needed findings; those are not usable content.

The merged local checkpoint records 622 recovered, 11 review-needed, 157 failed, and 3,469 queued resources. It has 534 unique downloaded files (36,969,120 bytes); recovery raw currently includes 568 files (37 MB) because alternate content responses and deduplicated resource records do not equal unique content hashes. This raw checkpoint is local and ignored by Git; it has not been promoted into the reviewed source catalog. Source records, alternate archive responses, and physical files are different counts, and are reported separately here.

## Current reconstruction and verification

A fresh desktop browser comparison of the reviewed-source `/2013/` page against the May 29, 2021 Wayback reference shows the logo, navigation, photo scale and crop align; see `current-checkpoint.json`. This is agent visual inspection, not human approval. The `/2007/` landing is still a gap screen because no original page bytes have been recovered; `/2009/` currently lists recovered items and gaps separately only at the route level, and is not yet a faithful final edition. The static builder produces a gateway and separate `/2007/`, `/2009/`, and `/2013/` editions. Candidate output is clearly separate from promoted sources. The current candidate build contains 411 recovered pages, 723 source-gap placeholders, and 106 local source assets. The current unreviewed candidate checks at both `/` and `/bluescholars/` report two unresolved routes (three link occurrences). The reviewed-source build/check passes at both paths (57 recovered pages, 305 placeholders, 31 source assets) with no remote automatic asset dependency. This is an incomplete reviewed collection and is not release approval. See `current-checkpoint.json`.

The automated suite has 105 passing tests (including the new conservative recovery-artifact merge regression tests). Pages is not enabled. `source/review.json` still has `visual_reviewed: false` and `publish_approved: false`.

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

The manually dispatched GitHub Action is the current fallback for Wayback access. Run `38824767784` ended cancelled at the 90-minute job ceiling; its artifact was imported locally. The smaller continuation `38834361363` failed before processing because artifact extraction collided with tracked report files; the resume workflow has since been corrected. Resume its last saved `archive-recovery` artifact by passing its numeric run ID as `resume_run`; choose one `edition_era` per run. Download the resulting artifact into staging, inspect the checkpoint and raw files, then merge it without replacing newer local work. The workflow is retrieval-only and does not publish.
