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
- Wayback domain checkpoint: complete; report records 8,178 indexed captures. After importing the partial 2007 recovery artifact, the local state has 4,956 resource records and 8,362 capture rows attached (the saved acquisition report counted 8,178 rows before the merge). Capture metadata is not equivalent to recovered bytes.
- Promoted source catalog: 3,268 resource records; 97 unique files under `source/raw/` are tracked. The publication and visual-review flags remain false.
- The unreviewed candidate currently has 449 recovered pages, 4 derived pages, 765 placeholders, and 420 local source assets. The separate LiveJournal route includes eight archived HTML capture routes and 20 locally served 2007–2008 photos; the custom journal CSS is recovered, while the separate platform-wide CSS remains missing. Root and `/bluescholars/` candidate link checks now pass with zero errors; see [the current checkpoint](recovery-report/current-checkpoint.json).
- The suite passes 119 tests; see [verification](VERIFICATION.md).
- 2007 continuation `38840327453` completed and its artifact was merged locally. The current bounded 2009 continuation is run `38847782580`, resuming from `38840327453`; merge its artifact after completion. Earlier recovery `38834520393` retrieved 368 of 373 selected responses, and the dated-image builder defect is fixed and regression-tested.
- User-requested incomplete candidate preview is live at https://keithah.github.io/bluescholars/ from `gh-pages` commit `cc3ddeea338842c97ecbaa6970b591183faab384`; Pages run `38851321206` succeeded. `main` remains separate and its history is unchanged. Publication and visual-review flags remain false; the reviewed-release workflow is still gated.

## Remaining before publication

Complete and merge bounded per-era Wayback runs, exact image searches, and independent Common Crawl/Arquivo searches. The public Pages URL is a candidate preview only; do not describe it as a finished restoration or mark review flags true. The smaller 2009 GitHub recovery-run candidate still reported `/2009/blog/tourdates/` as missing; the merged local preview has explicit gap routes and its current root and project-prefix checks pass. Preserve this runner/local difference in future artifact reports rather than treating either report as interchangeable. The 2007 batch `38834520393` recovered 368 of 373 selected responses but ended at candidate generation because of a dated image-variant bug; the builder fix is now covered by a regression test. The previous continuation `38834361363` failed before processing because of artifact extraction. Inspect newly recovered pages and image bytes, then reconcile the source and gap reports. Compare the rendered Squarespace homepage against the May 29, 2021 capture at desktop and mobile widths, and inspect the other editions and representative articles. Re-run release-mode and root/subpath checks on reviewed source files. Keep `source/review.json` false until source compatibility and visual review are honestly recorded.
