# Verification record — October 16, 2026

## Automated checks

- `.venv311/bin/python -m pytest -q` — **124 passed** (including homepage card and unreviewed-redirect regressions).
- `.venv311/bin/python -m compileall -q restore tests` — passed.
- `bash -n scripts/*.sh` — passed.
- `git diff --check` on implementation, tests, and documentation — passed. Original archived HTML is preserved byte-for-byte, including its source whitespace, so the check excludes `source/raw/` and its original-HTML test fixture.
- `actionlint .github/workflows/*.yml` — passed.
- After adding explicit notices/bridges without copying pages across historical editions, the root and `/bluescholars/` candidate checks pass with zero local-link errors. The `/lj/` pages have no broken local links or automatic remote resources.
- Reviewed-source build/check at `/` — passed (57 recovered pages, 305 placeholders, 31 local source assets).
- Reviewed-source build/check at `/bluescholars/` — passed with the same counts and no remote automatic asset dependency.
- The checker verifies no broken local links or automatic remote resources. External navigation links, such as historical social profiles and video links, remain ordinary anchors.

Latest offline candidate verification, rebuilt from the locally merged checkpoint on October 16: root and `/bluescholars/` checks each pass with zero link errors. The candidate contains 916 recovered pages, 1,916 placeholders, 4 derived pages, and 628 local source assets. Its build report still lists 4,085 missing assets, 295 linked assets not recovered, 144 external-media links, and 9 provider-error source records; those are source gaps, not checker errors. This checkpoint predates the active broad run `38878544130`, whose artifact has not yet been merged. The live preview is not release approval, and these checks do not satisfy the release gate.

## Repository and Pages

- GitHub CLI login: `keithah`; `repo` and `workflow` scopes are present.
- Target repository: public `keithah/bluescholars`, default branch `main`.
- At the owner’s direct request, the current unreviewed candidate was deployed as a public preview from the `gh-pages` branch. GitHub Pages API reports `built`; `source/review.json` remains false and the reviewed-release workflow remains gated.
- Live URL: [https://keithah.github.io/bluescholars/](https://keithah.github.io/bluescholars/). Pages build run [38851321206](https://github.com/keithah/bluescholars/actions/runs/38851321206) succeeded. Source branch commit: `cc3ddeea338842c97ecbaa6970b591183faab384`; it is separate from `main` and preserves main history.
- Live HTTP checks returned 200 for the root gateway, `/2007/`, `/2009/`, `/2013/`, `/lj/`, archive status, a WordPress pagination page, a 2009 article, a Squarespace article, and the archive UI CSS; an unknown route returned 404. The root’s year and LJ anchors point at the expected project-prefixed paths. Root and `/bluescholars/` automatic-resource/link checks pass locally.
- No screenshot file was saved. Browser-panel automation timed out during live navigation; route and asset checks were performed directly over HTTPS.

## Visual review

The reviewed local `/2013/` page was opened alongside the May 29, 2021 archive capture earlier in this continuation. At desktop width, the ribbon logo, navigation, sidebar spacing, photograph crop, and main image position match; the vertical offset is accounted for by the Wayback toolbar height versus the local restoration notice. The project-subpath rendering was also opened in the browser; CSS, logo, and hero photograph loaded from the local preview. The homepage image and recovered ribbon logo both rendered. At 390×844, the local page collapsed the navigation to the original mobile “Menu” treatment and displayed the photograph within the viewport. The browser did not apply that viewport override to the separate archive tab, so a pixel-matched mobile screenshot comparison remains open.

The project-subpath page at `http://127.0.0.1:8080/bluescholars/2013/` rendered in the same browser with the same local image and navigation destinations under `/bluescholars/`. These are agent observations; no human review is claimed. The site-wide review is still incomplete: the 2007 edition remains an explicit no-page-bytes gap, and the 2009 landing page currently mixes a few recovered routes with many route-gap entries. No human review is claimed, so visual/publication flags stay false.

## Known limitations

- Recovery coverage is not exhaustive yet. See [the recovery report](recovery-report/RECOVERY_REPORT.md) and [the gap report](recovery-report/GAP_REPORT.md).
- The offline checker establishes local consistency, not full historical completeness or pixel fidelity.
- No original font binaries are bundled. Archived video players are represented as external links; no video files were recovered.


## LiveJournal archive preview

The root gateway now links to `/lj/`, separate from the three official website generations. The browser preview at `http://127.0.0.1:8083/lj/` and the project-path preview at `http://127.0.0.1:8084/bluescholars/lj/` each showed the eight capture routes; the individual 2007 post retained its text/comments and six local photos. A browser screenshot was visually inspected in-session but no screenshot file was saved. The custom stylesheet was recovered after this preview; its built output now serves it locally, while the LiveJournal platform CSS bundle remains missing and that preview did not verify the original design.


The October 2011 LiveJournal captures were checked in the browser at both root and project-prefix previews. The `/lj/` index lists all eight saved HTML capture routes with dates. The custom journal CSS is now local, while the separate LiveJournal platform bundle remains unavailable. Candidate generation/check passed independently for `/` and `/bluescholars/` (449 recovered pages, 4 derived pages, 765 placeholders, 420 local assets, zero link errors). This is technical verification, not a human visual approval or release sign-off.

A direct scan of the generated candidate HTML (`src`, `poster`, embedded data, and stylesheets) and CSS (`url()`) found zero automatic remote resource references. External web links remain ordinary clickable links.

The exact October and August LiveJournal custom stylesheet captures are byte-identical (7,343 bytes, SHA-256 `87560599e9fb5ddc5cdba0675164f3bd80324540d346fc6ae38c26878e2f34ce`). Builder recovery now excludes CSS assets from its HTML-page route loop and emits the custom stylesheet locally. The separate LiveJournal platform CSS URLs remain missing.

Four LiveJournal entry pages without standalone captures now render their exact saved `.entry` blocks from the October 2011 index, visibly state their source and capture date, and disclose the missing standalone comment threads. Browser inspection confirmed the entry text and source disclosure at the project prefix.


## 2026-10-16 homepage and merged-candidate checks

- GitHub CI run `38960837794` passed the test suite and reviewed-source builds/checks at `/` and `/bluescholars/`.
- Local suite after the homepage and redirect changes: `PYTHONPATH=. .venv311/bin/pytest -q` — 124 passed.
- Local unreviewed candidate from merged recovery state through run `38960473470`: 916 recovered pages, 1,875 placeholders, 727 local source assets; `/bluescholars/` checker passed with zero errors after redirect correction. The runner check on that earlier code revision had 76 broken `/2009/menu/` links.
- Local browser view of the candidate gateway confirmed three edition cards with era labels, and secondary LiveJournal/recovery links. This is an agent visual inspection, not human release approval. No screenshot file was saved.
- At this checkpoint Pages had not yet been refreshed; see the newer preview deployment entry below.


## Recovery continuation update — October 16, 2026

- 2013+ Wayback pass `38960845000` completed: 171 URL captures attempted and 11 valid HTML responses recovered. Merge added 22 resource records and copied six new raw files; 1,660 file hashes duplicated bytes already stored. The Arquivo.pt step reported 35 domain-index rows and no new response bodies.
- Consolidated local checkpoint after merge: 8,602 resource URLs; 2,635 recovered, 48 needs review, 1,019 failed and 4,900 queued; 8,992 capture rows; 1,943 unique files totaling 105,704,279 bytes.
- Broad Wayback run `38962246474` is active. A separate Common Crawl run `38972843891` is queued behind it (up to 3,000 records).
- Candidate rebuild from this newly merged checkpoint has not yet been verified; the build command encountered a local generated-output directory cleanup error. The previously documented successful candidate check predates this merge.
- `source/review.json` still has `publish_approved: false` and `visual_reviewed: false`; the later deployment is only an owner-requested partial preview, not release approval.

The candidate was rebuilt locally from the merged checkpoint through run `38960845000`. It contains 922 recovered pages, 1,871 placeholders, four derived LiveJournal views and 727 local source assets. Candidate checks pass with zero local-link errors at both `/` and `/bluescholars/`. These checks establish path/link consistency, not completeness or release approval. The independent Common Crawl follow-up remains queued; see the current checkpoint for live run state.

## Recovery continuation update — October 16, 2026 (run 38962246474)

- The broad acquisition hit the 90-minute cap. Its always-run candidate generation and artifact upload succeeded; the runner candidate check passed with zero errors. Merge imported three additional raw files, 61 CDX batches, 23 new resources and 144 dated variants, with no conflicts.
- Consolidated local checkpoint: 8,769 resource URLs; 2,881 recovered, 50 needs review, 1,120 failed and 4,718 queued; 9,210 capture rows; 1,946 unique files totaling 107,189,680 bytes.
- Rebuilt candidate at root and `/bluescholars/`: 922 recovered pages, 1,842 placeholders, four derived views and 729 local source assets. Both candidate checks passed with zero local-link errors. Build report gaps: 4,037 missing embedded assets, 295 linked assets not recovered, 145 external media links, 17 fonts not packaged and 9 invalid source records.
- Common Crawl independent run `38972843891` is active (up to 3,000 records), resuming from `38962246474`.
- The latest gateway and recovery snapshot were subsequently published as a partial preview; release approval flags remain false.


## Updated public preview — October 16, 2026

- Pushed the generated `/bluescholars/` candidate as commit `903ee0acc230c42636ba2ebd28ea0b1f6f840028` on `gh-pages`, parent `cc3ddeea338842c97ecbaa6970b591183faab384`. This is a fast-forward commit; history is preserved. The candidate contains 3,383 files (76,770,346 bytes) and `.nojekyll`.
- GitHub Pages deployment run [38976443204](https://github.com/keithah/bluescholars/actions/runs/38976443204) succeeded; API reports `built` from `gh-pages` at `/`. Live HTTP checks returned 200 for `/bluescholars/`, `/2007/`, `/2009/`, `/2013/`, `/lj/`, `/archive-status/`, the main CSS and a recovered 2009 Paul Valéry post; an unknown route returned 404. Browser inspection showed the three separate edition cards and secondary links. No screenshot file was saved.
- The preview is still incomplete and unreviewed. `source/review.json` remains `publish_approved: false`, `visual_reviewed: false`. The reviewed release workflow remains gated; this preview refresh does not claim the restoration is complete.

## October 17 continuation and refreshed preview

- `.venv311/bin/python -m pytest -q` — **125 passed**.
- `.venv311/bin/python -m compileall -q restore tests` and `git diff --check` — passed.
- Candidate built and checked at `/` and `/bluescholars/` after merge of run 38975520061 — both checks passed with zero errors, including zero remote automatic-resource errors.
- Refreshed candidate: 924 recovered pages, 1,851 placeholders, four derived LJ views, and 732 local assets. The remaining measured source gaps are in `docs/recovery-report/GAP_REPORT.json`.
- Code commit `413c4b6` pushed to `main`; CI run [38985439462](https://github.com/keithah/bluescholars/actions/runs/38985439462) was still running at this report update.
- Unreviewed preview commit `a507923` pushed fast-forward to `gh-pages`; Pages build/deploy [38985421271](https://github.com/keithah/bluescholars/actions/runs/38985421271) succeeded and the Pages API reports `built`. Live browser accessibility inspection confirmed the three year/era cards and secondary LJ/status links. HTTPS checks returned 200 for `/`, `/2007/`, `/2009/`, `/2013/`, `/lj/`, `/archive-status/`, `/2013/blog/`, the UI stylesheet, and a recovered 2011 WordPress post; an unknown route returned 404. Gateway markup had three edition links and no automatically loaded remote assets.
- The live 2011 post route `/bluescholars/2009/blog/update-cinemetropolis-advance-digital-download-out-now-official-release-date-june-14/` returned the recovered article and May 17, 2011 date. Its May 20 Wayback source capture and July/2012 alternatives are individually documented in `capture-compatibility.json`.
- No screenshot file was saved in this continuation. Browser review was agent-performed; no human review is claimed. Visual-fidelity and publication flags remain false.

## October 17 continuation — legacy editions and same-crawl Squarespace assets

- Current baseline in this workspace: `PYTHONPATH=. .venv311/bin/pytest -q` — **140 passed**. Plain `.venv311/bin/pytest -q` without `PYTHONPATH=.` fails collection because this package layout is not installed into the environment; the documented invocation with the project root on the import path passes.
- `.venv311/bin/python -m compileall -q restore tests`, `bash -n scripts/*.sh`, `actionlint .github/workflows/*.yml`, and `git diff --check` all pass.
- Fresh candidate builds were checked at the domain root and project path: each reports 955 recovered pages, 2,357 placeholders, four derived LiveJournal views and 750 local source assets. Both `restore check` results are `{ "ok": true, "errors": [] }`. Build findings remain 5,352 missing embedded assets, 319 unrecovered linked assets, 145 external media links, 27 omitted fonts, and nine invalid/provider-error records. A clean checker result does not mean all those sources were recovered.
- Local browser inspection confirms the 2007 homepage at `20070724082915` displays all seven locally recovered original panel GIFs and its historical July 2007 show listings; the 2009 SXSW article displays its March 2009 text, four comments, original theme/sidebar assets; and the May 29, 2021 Squarespace page displays its historical navigation/layout, same-crawl ribbon logo, and original front-page photograph. The correct linked Squarespace CSS was captured at `20210529010844`, 27 seconds after the homepage, and serves locally. This is agent-performed inspection only. No screenshot file was saved, so there is no saved visual-comparison artifact or human review.
- Resource compatibility notes were added to `docs/recovery-report/capture-compatibility.json`; the exact URL, capture time and hash for every inspected source are in the recovery state and per-edition report. Later-capture approvals remain resource-specific. `source/review.json` still has `publish_approved: false` and `visual_reviewed: false`.
- The latest local recovery state contains 10,093 URLs, 22,579 indexed captures, 2,095 unique raw files / 112,816,864 bytes, and statuses 3,310 recovered, 64 needs-review, 1,311 failed and 5,408 queued. The detailed gap report distinguishes these counts and notes the 2008 compromised root exclusion.
- Any deployed refresh remains the already-authorized **unreviewed candidate preview**, not a completed release. The strict release gates remain unmet because of the remaining source gaps and absence of a saved visual-comparison artifact/human approval; do not set the review flags to work around them.
