# Implementation and release status — October 16, 2026

## What is implemented

- A resumable Wayback CDX inventory with raw index batches and dated exact-capture variants.
- Static editions separated at `/2007/`, `/2009/`, and `/2013/`, with a gateway at the root and a separate `/lj/` archive for LiveJournal captures.
- Candidate and reviewed-source build modes, local asset rewriting, capture provenance, an offline link/resource checker, and project-subpath handling.
- Independent Common Crawl WARC/ARC retrieval and Arquivo.pt capture retrieval.
- Targeted exact-CDX indexing of the 42 observed source-linked image URLs.
- A manual, non-publishing GitHub Actions recovery workflow. It can continue from an earlier run's artifact.

## Current evidence

- Public repository: `https://github.com/keithah/bluescholars`, branch `main`; authenticated GitHub CLI account `keithah`.
- Wayback domain checkpoint: complete; report records 8,178 indexed captures. After importing the partial 2007 recovery artifact, the local state has 4,259 resource records and 8,319 capture rows attached (the saved acquisition report counted 8,178 rows before the merge). Capture metadata is not equivalent to recovered bytes.
- Promoted source catalog: 3,268 resource records; 97 unique files under `source/raw/` are tracked. The publication and visual-review flags remain false.
- The unreviewed candidate currently has 446 recovered pages, 758 placeholders, and 417 local source assets. The separate LiveJournal route includes five archived HTML captures and 20 locally served 2007–2008 photos; its original CSS remains missing. Root and `/bluescholars/` candidate checks each expose three link occurrences across two unresolved routes; see [the current checkpoint](recovery-report/current-checkpoint.json).
- The suite passes 114 tests; see [verification](VERIFICATION.md).
- The 2007 action `38834520393` recovered 368 of 373 selected responses, then its candidate build failed on a dated image-variant key. That code defect is fixed and tested; the workflow still needs a rerun. The previous `38834361363` continuation failed before acquisition during artifact extraction.
- Pages API returned 404 when checked, so Pages is disabled. No deployment URL exists yet.

## Remaining before publication

Complete and merge bounded per-era Wayback runs, exact image searches, and independent Common Crawl/Arquivo searches. Add or recover the two remaining candidate route targets (`/2009/blog/tourdates/` and `/2013/archive-query/27bed984677400b185e8/`) without aliasing incompatible source generations. The 2007 batch `38834520393` recovered 368 of 373 selected responses but ended at candidate generation because of a dated image-variant bug; the builder fix is now covered by a regression test. The previous continuation `38834361363` failed before processing because of artifact extraction. Inspect newly recovered pages and image bytes, then reconcile the source and gap reports. Compare the rendered Squarespace homepage against the May 29, 2021 capture at desktop and mobile widths, and inspect the other editions and representative articles. Re-run release-mode and root/subpath checks on reviewed source files. Keep `source/review.json` false until source compatibility and visual review are honestly recorded.
