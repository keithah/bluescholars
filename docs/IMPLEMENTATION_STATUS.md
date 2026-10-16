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
- Wayback domain inventory is complete. The consolidated checkpoint contains 8,602 resource URLs and 8,992 indexed capture rows: 2,635 recovered, 48 held for review, 1,019 failed, and 4,900 queued. It has 1,943 unique downloaded files (105,704,279 bytes). Run `38948396209` added 4 raw files, 29 CDX index batches, 85 resources and 17 dated variants before hitting the acquisition time limit; no conflicts.
- Per-era recovery: 2007 continuation `38956253558` attempted four remaining eligible URLs and recovered none; 2009 pass `38960473470` attempted 41 URLs and recovered two responses (a 2012 post and an image); 39 endpoints failed. The 2013+ pass `38960845000` completed: 171 URLs attempted, 11 valid responses recovered, 22 new resource records and six newly copied raw files (1,660 hashes deduplicated). The broad continuation `38962246474` is active. Common Crawl follow-up `38972843891` is queued behind it, configured for up to 3,000 independent WARC responses. The separate 2007 site remains only partially represented.
- The local merged candidate has 916 recovered pages, four derived LiveJournal views, 1,875 placeholders, and 727 local source assets; its `/bluescholars/` link check passes. A project-prefix check now passes after fixing an unsafe rewrite from a needs-review 2025 restaurant redirect; the first runner check had 76 broken `/2009/menu/` links. Build gaps remain: 4,033 embedded assets, 295 linked assets, 17 fonts, and other source issues. This is not evidence of full visual fidelity.
- Homepage gateway now uses three year/era cards and secondary links for LiveJournal and recovery status. The `/bluescholars/` candidate was viewed in a local browser. Commit `151b51a` has the visual change; commit `40b07f3` fixes redirect handling. GitHub CI `38960837794` passed tests and root and project-prefix reviewed-source build/checks; local suite: 124 passed.
- Promoted source catalog: 3,268 resource records; 97 unique files under `source/raw/` are tracked. `source/review.json` publication and visual-review flags remain false. The public candidate at `https://keithah.github.io/bluescholars/` is still served from `gh-pages` commit `cc3ddeea338842c97ecbaa6970b591183faab384`; the new homepage commit has not been deployed. Publication and visual-review flags remain false.

## Remaining before publication

Complete and merge bounded per-era Wayback runs, exact image searches, and independent Common Crawl/Arquivo searches. The public Pages URL is a candidate preview only; do not describe it as a finished restoration or mark review flags true. The smaller 2009 GitHub recovery-run candidate still reported `/2009/blog/tourdates/` as missing; the merged local preview has explicit gap routes and its current root and project-prefix checks pass. Preserve this runner/local difference in future artifact reports rather than treating either report as interchangeable. The 2007 batch `38834520393` recovered 368 of 373 selected responses but ended at candidate generation because of a dated image-variant bug; the builder fix is now covered by a regression test. The previous continuation `38834361363` failed before processing because of artifact extraction. Inspect newly recovered pages and image bytes, then reconcile the source and gap reports. Compare the rendered Squarespace homepage against the May 29, 2021 capture at desktop and mobile widths, and inspect the other editions and representative articles. Re-run release-mode and root/subpath checks on reviewed source files. Keep `source/review.json` false until source compatibility and visual review are honestly recorded.
