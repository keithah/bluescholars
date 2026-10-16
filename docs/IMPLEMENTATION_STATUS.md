# Implementation and release status — October 16, 2026

## What is implemented

- A resumable Wayback CDX inventory with raw index batches and dated exact-capture variants.
- Static editions separated at `/2007/`, `/2009/`, and `/2013/`, with a gateway at the root and a separate `/lj/` archive for LiveJournal captures.
- Candidate and reviewed-source build modes, local asset rewriting, capture provenance, an offline link/resource checker, and project-subpath handling.
- Independent Common Crawl WARC/ARC retrieval and Arquivo.pt capture retrieval.
- Targeted exact-CDX indexing of the 42 observed source-linked image URLs.
- A bounded, non-publishing GitHub Actions recovery workflow. Runs continue from a prior artifact; a local controller is advancing batches and merging each finished artifact.

## Current evidence

- Public repository: `https://github.com/keithah/bluescholars`, branch `main`; authenticated GitHub CLI account `keithah`.
- Wayback domain checkpoint: complete; local state currently has 8,348 resource URLs and 8,904 indexed capture records. At the last merged checkpoint, 5,843 URLs remained queued, 2,239 were recovered, 29 needed review, and 237 had failed; 1,872 unique raw files (99,127,968 bytes) were present. Capture metadata is not equivalent to recovered bytes. The broad run `38878544130` is still acquiring; its artifact has not yet been merged.
- Promoted source catalog: 3,268 resource records; 97 unique files under `source/raw/` are tracked. The publication and visual-review flags remain false.
- The current unreviewed candidate has 916 recovered pages, 4 derived pages, 1,916 placeholders, and 628 local source assets. Candidate link checks pass with zero errors at both `/` and `/bluescholars/`; it still reports 4,085 missing assets and 9 provider-error sources. See [the current checkpoint](recovery-report/current-checkpoint.json).
- The suite passes 120 tests; see [verification](VERIFICATION.md). A new regression guards against failed high-priority URLs starving untouched pages.
- Latest merged checkpoint: run `38873762766`. Broad recovery `38878544130` is in progress; queued follow-up `38880249610` uses the corrected queue order and resumes from it. Continue from the latest completed run artifact if the local continuation is interrupted.
- User-requested incomplete candidate preview is live at https://keithah.github.io/bluescholars/ from `gh-pages` commit `cc3ddeea338842c97ecbaa6970b591183faab384`; Pages run `38851321206` succeeded. New recovery-tool and ledger commits are on `main`; they do not change the published preview. Publication and visual-review flags remain false, and the reviewed-release workflow is still gated.

## Remaining before publication

Complete and merge bounded per-era Wayback runs, exact image searches, and independent Common Crawl/Arquivo searches. The public Pages URL is a candidate preview only; do not describe it as a finished restoration or mark review flags true. The smaller 2009 GitHub recovery-run candidate still reported `/2009/blog/tourdates/` as missing; the merged local preview has explicit gap routes and its current root and project-prefix checks pass. Preserve this runner/local difference in future artifact reports rather than treating either report as interchangeable. The 2007 batch `38834520393` recovered 368 of 373 selected responses but ended at candidate generation because of a dated image-variant bug; the builder fix is now covered by a regression test. The previous continuation `38834361363` failed before processing because of artifact extraction. Inspect newly recovered pages and image bytes, then reconcile the source and gap reports. Compare the rendered Squarespace homepage against the May 29, 2021 capture at desktop and mobile widths, and inspect the other editions and representative articles. Re-run release-mode and root/subpath checks on reviewed source files. Keep `source/review.json` false until source compatibility and visual review are honestly recorded.
