# Implementation and release status — October 15, 2026

## What is implemented

- A resumable Wayback CDX inventory with raw index batches and dated exact-capture variants.
- Static editions separated at `/2007/`, `/2009/`, and `/2013/`, with a gateway at the root.
- Candidate and reviewed-source build modes, local asset rewriting, capture provenance, an offline link/resource checker, and project-subpath handling.
- Independent Common Crawl WARC/ARC retrieval and Arquivo.pt capture retrieval.
- Targeted exact-CDX indexing of the 42 observed source-linked image URLs.
- A manual, non-publishing GitHub Actions recovery workflow. It can continue from an earlier run's artifact.

## Current evidence

- Public repository: `https://github.com/keithah/bluescholars`, branch `main`; authenticated GitHub CLI account `keithah`.
- Wayback domain checkpoint: complete; report records 8,178 indexed captures. After importing the partial 2007 recovery artifact, the local state has 4,259 resource records and 8,319 capture rows attached (the saved acquisition report counted 8,178 rows before the merge). Capture metadata is not equivalent to recovered bytes.
- Promoted source catalog: 3,268 resource records; 97 unique files under `source/raw/` are tracked. The publication and visual-review flags remain false.
- The unreviewed candidate currently has 411 recovered pages, 723 placeholders, and 106 local source assets. After the partial artifact merge, root and `/bluescholars/` checks both expose three links that still need recovery or an explicitly labeled bridge page; see [the current checkpoint](recovery-report/current-checkpoint.json).
- The suite passes 105 tests; see [verification](VERIFICATION.md).
- A prior recovery action successfully saved its checkpoint and downloaded material but failed its candidate build because an old provider-error response remained marked recovered. The builder now records invalid source bytes as a gap; the regression test passes. The next run uses the repaired builder.
- Pages API returned 404 when checked, so Pages is disabled. No deployment URL exists yet.

## Remaining before publication

Complete and merge bounded per-era Wayback runs, exact image searches, and independent Common Crawl/Arquivo searches. The 2007 batch `38824767784` timed out before its edition and Arquivo steps; a resumable follow-up is queued as `38834361363`. Inspect newly recovered pages and image bytes, then reconcile the source and gap reports. Compare the rendered Squarespace homepage against the May 29, 2021 capture at desktop and mobile widths, and inspect the other editions and representative articles. Re-run release-mode and root/subpath checks on reviewed source files. Keep `source/review.json` false until source compatibility and visual review are honestly recorded.
