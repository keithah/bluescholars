# Blue Scholars historical recovery report

**Updated:** October 16, 2026. **Scope:** separate copies of the 2007, 2009/WordPress, and Squarespace-era sites, with the May 29, 2021 homepage as the Squarespace visual reference.

## Evidence collected

### Internet Archive Wayback Machine

The saved domain CDX checkpoint is marked complete. Its acquisition report records 8,178 capture rows. After the 2007 batch import and subsequent source-linked LiveJournal, image, TIFF, and Common Crawl acquisitions, the current local checkpoint contains 4,893 resource records and 8,362 attached capture rows. Capture metadata is not equivalent to recovered response bodies. The original run's domain scan has raw CDX batches preserved locally under `recovery/index/`; those generated working files are excluded from Git. A complete capture index describes available snapshots; it does not mean their response bodies have been downloaded.

Before the targeted exact image-host queries were added, the state exposed these latest-200-OK selections per URL: 373 resources in the 2007 date range, 799 in the 2009-to-pre-Squarespace range, and 193 in the Squarespace range. They are selection counts, not acquisition success counts. Use the `capture-era` command or the updated recovery workflow to fetch each selected dated response while preserving variants.

The existing selected homepage body is genuine HTML from `20210529010817`. Its reference photograph is separately identified at `20210529010844`, 27 seconds later. This is preserved as a resource-specific same-crawl dependency. The selected homepage CSS and the 2020 section pages are also present in the recovered source set. A Shop response captured in 2020 is a provider error; the raw bytes and provenance remain in recovery metadata but are not treated as shop content.

### Common Crawl

The initial local all-collection index sweep found 128 published index endpoints but reached only 6; 122 requests failed from that machine. Those six returned 380 unique domain responses, all acquired as original WARC records with collection, filename, offset, length, digest, and content hash recorded. Many are WordPress-era pages from the 2016/2017 crawls. This is useful independent evidence but is **not** full Common Crawl coverage.

Two additional collection queries were saved as reproducible JSONL seeds in `recovery/seeds/commoncrawl/`:

- `CC-MAIN-2009-2010.jsonl`: 19 valid archived site pages were fetched, including blog/article, bio, release, tour, and store routes from the early WordPress site.
- `CC-MAIN-2023-40.jsonl`: 5 page bodies were recovered from 16 relevant rows. Three `robots.txt` rows were rejected as non-HTML; the archived Shop response was rejected as a provider error. A captured blog/homepage response supplies a late Squarespace-era comparison point.

Common Crawl uses independent snapshots; identical capture hashes are deduplicated in storage but source rows remain documented. These captures do not replace Wayback captures from the requested editions.

### Arquivo.pt

The Arquivo.pt root-history query returned 12 capture rows from 2017–2023, including three successful original HTML responses from April 2018, July 2018, and October 2019. A live domain CDX scan returned 35 rows; its bounded selector retrieved the 2019 homepage and blog listing plus the 2018 favicon (three valid bodies, no failures). The blog listing contains twenty visible post cards; all eighteen internal post links were queried through Arquivo.pt exact version history, which returned zero captures. The associated article pages are already present from Common Crawl. Domain index and acquisition details are in [OTHER_ARCHIVES.json](OTHER_ARCHIVES.json) and the checkpoint files.

### Other archive checks

The Library of Congress catalog returned zero exact-name/domain records, while its wildcard replay endpoint returned HTTP 403 from this environment. Archive-It public full-text search located a 2009 Blue Scholars Twitter profile capture and related third-party sources; the individual replay was viewed in the browser. Its documented global `/all` CDX endpoint returned HTTP 403. Archive.today's index revealed one January 2013 homepage capture, but snapshot retrieval hit a CAPTCHA/security response. Trove access was stopped at an Anubis anti-bot page; the UK Web Archive lookup redirected to an error page, and Ghostarchive's exact homepage query returned no archives. These are service/search outcomes, not archive-wide absence findings. See the detailed [independent archive report](OTHER_ARCHIVES.md).

## Current saved source collection

`source/catalog.json` contains 3,268 inventory records. It points to 97 unique content-addressed original files in `source/raw/` (about 11.5 MB): 126 source records reference HTML bytes, 28 reference CSS bytes, and 3 reference image bytes. Several records intentionally share the same physical file by hash. The catalog also retains queued, failed, and review-needed findings; those are not usable content.

The local recovery checkpoint currently records 1,034 recovered, 14 review-needed, 156 failed, and 3,752 queued resources. It has 844 unique downloaded files (64,208,197 bytes). The latest local refresh is in `current-checkpoint.json`; the checkpoint and raw response files are ignored by Git and must be preserved separately before changing machines. Recovery raw is local and ignored by Git. Arquivo.pt and Wayback additions remain outside the reviewed source collection unless individually reviewed and promoted.

## Current reconstruction and verification

A desktop browser comparison of the May 29, 2021 baseline and the September 30, 2023 Wayback homepage shows the same logo, navigation, hero photograph, crop, and layout. The later HTML is byte-identical to Common Crawl's September 27, 2023 capture. This is agent visual inspection, not human approval. The builder keeps separate `/2007/`, `/2009/`, and `/2013/` editions, plus a separately hosted `/lj/` LiveJournal archive. Candidate counts are 449 recovered pages, 769 placeholders, and 419 source assets. Root and `/bluescholars/` candidate checks each retain previously unresolved WordPress and cross-era links now have an explicit gap notice or a bridge to the recovered page in its original edition. Root and `/bluescholars/` candidate link checks pass with zero errors. The eight recovered LiveJournal capture routes and 20 historically dated photos live in the ignored local recovery checkpoint, not the reviewed catalog. The reviewed-source build/check passes at root and `/bluescholars/` (57 recovered pages, 305 placeholders, 31 assets, zero automatic remote dependencies), but it remains incomplete and is not release approval.

The automated suite has 118 passing tests (including the new conservative recovery-artifact merge regression tests). Pages is not enabled. `source/review.json` still has `visual_reviewed: false` and `publish_approved: false`.

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

The manually dispatched GitHub Action is the current fallback for Wayback access. Run `38834520393` preserved the 2007-era retrieval artifact (368 of 373 selected resources recovered) but ended when candidate build hit a dated image-variant key bug; that builder defect is now fixed and covered by a regression test, but the workflow has not yet been rerun with the fix. Run `38824767784` ended cancelled at the 90-minute job ceiling; its artifact was imported locally. The smaller continuation `38834361363` failed before processing because artifact extraction collided with tracked report files; the resume workflow has since been corrected. Resume its last saved `archive-recovery` artifact by passing its numeric run ID as `resume_run`; choose one `edition_era` per run. Download the resulting artifact into staging, inspect the checkpoint and raw files, then merge it without replacing newer local work. The workflow is retrieval-only and does not publish.


### Separate LiveJournal archive

A source-linked LiveJournal journal was recovered from Wayback and Common Crawl. The `/lj/` section uses the latest old-layout captures from October 2, 2011 for its front page and two individual 2007 posts. Earlier January 2009 and August 2011 page variants are retained under dated capture routes, alongside a 2010 Common Crawl root response and a 2009 Common Crawl profile. The 2011 index includes six complete visible 2007–2008 entry texts; only two have standalone post captures. Twenty 2007–2008 photos are locally mapped. The custom LiveJournal stylesheet is recovered; exact platform CSS history queries returned no successful framework bundles, the later Eventful poster is withheld pending date review, and one Massline Media image resolves only to a Wayback lander. This separate host is not counted as one of the three official website generations; see [independent archive findings](OTHER_ARCHIVES.md).
