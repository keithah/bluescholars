# Verification record — October 16, 2026

## Expanded Mass Line forum recovery — October 19, 2026

- `.venv311/bin/python -m pytest -q`: **235 passed**. The dotted-directory route regression failed before the fix and passes afterward.
- The selected-era Mass Line recovery is complete for its indexed queue: 4,742 validated resources, five homepage variants, 473 invalid/unavailable responses, zero pending. The all-capture event query contains 7,121 rows; all 5,276 distinct forum URL/date records are accounted for, with 1,215 separately stored alternate source versions and 496 invalid/unavailable variant responses.
- Mass Line renderer report: 4,418 generated pages, nine boards, 565 topics with local saved views, 277 dated board listings, 1,193 alternate HTML pages, 5,901 compatibility redirects and 797 local Mass Line assets. The preview build is approximately 518 MB.
- The `/bluescholars/` candidate and separate domain-root candidate both pass `restore check` with `{ "ok": true, "errors": [] }`. Automatic assets are local. The offsite source index covers 1,531 exact URLs: 474 recovered images, 1,026 confirmed no-capture results, 29 unusable archive responses, two Wayback CDX 403 failures and zero queued URLs. All 1,531 discovered external image URLs have an outcome; no external audio/video files were recovered. The search is resumable if new source links are found with `.venv311/bin/python -m restore massline-external-index --max-assets 80 --delay 0.8`, followed by `massline-external-recover`; source URLs, dated CDX records, digests, raw paths and referring forum pages are preserved.
- The Pages preview remains an unreviewed candidate, and release approval flags remain false. Pages preview commit `1f4c34a4` deployed from `gh-pages`; workflow [39337254570](https://github.com/keithah/bluescholars/actions/runs/39337254570) passed and Pages API reports `built`. Live HTTPS returned 200 for `/`, `/bluescholars/`, the forum index, board 1, a dated 2007 topic, and eight newly recovered image URLs. The generated `/bluescholars/` candidate check returned `{ "ok": true, "errors": [] }`; `.venv311/bin/python -m pytest -q` passed (235 tests). Browser accessibility and screenshot inspection confirmed the live board title list, saved dated views, and forum navigation. Browser accessibility and screenshot inspection were agent-performed; no screenshot file was saved, no human review is claimed, and publication approval flags remain false.

## Mass Line forum archive split — October 19, 2026

- The SMF forum is now a standalone top-level archive at `/massline-forums/`, separate from the Mass Line Media site restoration at `/masslinemedia/`. The main gateway has separate cards, and the dated Mass Line homepage links to the forum archive.
- The forum directory includes 9 captured boards and 239 topic IDs with locally saved views. Source captures and SMF assets are emitted under the forum directory. The former `/masslinemedia/forum/` paths have 1,638 generated same-site compatibility redirects.
- `.venv311/bin/pytest -q` — **232 passed**. `git diff --check` passed for source changes. Candidate build/check at `/bluescholars/` passed; root-path candidate build/check also passed with `{ "ok": true, "errors": [] }`. The root output was built separately; the previously saved `_site/` directory was restored without changes.
- Generated candidate inspection confirmed the gateway’s `/massline-forums/` link, board listing paths, and legacy redirects. No screenshot or human visual review was performed. This remains an unreviewed preview; no source review flags were changed.
- Source commit `6ccfb3c7` (`Separate Mass Line forum archive at top level`) was pushed to `main`. The Pages preview is a separate fast-forward snapshot: final `gh-pages` commit `47872571` follows `761870c9`; GitHub Pages deployment [39303399989](https://github.com/keithah/bluescholars/actions/runs/39303399989) completed successfully and the Pages API reports `built`.
- Live HTTPS checks returned 200 for `/bluescholars/`, the new forum directory, board 1, topic 66, the Mass Line homepage, and both the legacy forum root and topic redirect pages. The page links and redirect targets include the `/bluescholars/` project prefix. The gateway card and board link resolve to the standalone forum area.
- No screenshot or human visual review was performed; this remains an unreviewed candidate preview. `source/review.json` and reviewed-release gates were not changed.

## Mass Line forum archive split — October 19, 2026

- The SMF forum is now a standalone top-level archive at `/massline-forums/`, separate from the Mass Line Media site restoration at `/masslinemedia/`. The main gateway has separate cards, and the dated Mass Line homepage links to the forum archive.
- The forum directory includes 9 captured boards and 239 topic IDs with locally saved views. Source captures and SMF assets are emitted under the forum directory. The former `/masslinemedia/forum/` paths have 1,638 generated same-site compatibility redirects.
- `.venv311/bin/pytest -q` — **232 passed**. `git diff --check` passed for source changes. Candidate build/check at `/bluescholars/` passed; root-path candidate build/check also passed with `{ "ok": true, "errors": [] }`. The root output was built separately; the previously saved `_site/` directory was restored without changes.
- Generated candidate inspection confirmed the gateway’s `/massline-forums/` link, board listing paths, and legacy redirects. No screenshot or human visual review was performed. This remains an unreviewed preview; no source review flags were changed.
- Local execution completed only. No commit, push, or Pages redeployment has yet occurred.

## Artist-site editions — October 17, 2026

- `PYTHONPATH=. .venv311/bin/python -m pytest -q` — **181 passed**. `compileall -q restore tests` passed. `git diff --check` passed for code/docs/reports with byte-preserved `recovery/artist-sites/raw/` payloads excluded; their original CRLF whitespace remains intact.
- Candidate build/check at the domain root and at `/bluescholars/` both completed; `restore check` returned `{ "ok": true, "errors": [] }` for both. The checker scanned the rendered pages and stylesheets, including the new 11 artist-site editions, and found no remote automatic resource requests.
- The candidate contains 615 renderable artist-site pages and 381 local assets from 674 unique source payloads. Browser inspection confirmed the main gateway links to both hubs; Prometheus Brown’s 2009/2010 cards lead to the archived `/blog/` homes, and Sabzi’s cards lead to dated homepages. A 2010 WordPress blog page and the Sabzi 2019 homepage were opened locally.
- Visual inspection exposed real gaps: the Prometheus Brown 2010 theme stylesheet and several photographs have no usable capture; the Sabzi page’s remaining site-specific layout imagery is incomplete. Missing photographs now render as labeled gap markers linked to dated Wayback sources. Eight unsafe SVG payloads are preserved in the raw source collection but excluded from rendering. No replacement artwork or CSS was fabricated. 205 later-page captures await compatibility review.
- The capture/source records are in [artist-sites-report.json](recovery-report/artist-sites-report.json), with the human-readable summary in [artist-sites-report.md](recovery-report/artist-sites-report.md). The 2024 casino spam exclusions and source digests are recorded there; 2025–2026 Prometheus Brown rows remain indexed but uninspected.
- Browser checking was agent-performed; no screenshot file was saved and no human review is claimed. `source/artist-sites.json` is not promoted, `source/review.json` remains false for both publication and visual review, and Pages was not redeployed. These additions are still an unreviewed recovery candidate.

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


## Live candidate refresh — October 17, 2026

- `main` validation run [39001969501](https://github.com/keithah/bluescholars/actions/runs/39001969501) succeeded for commit `7d6f74cdc6bb9eba28d1dedd54a3bda5fce7384b`.
- Project Pages deployment [39001990053](https://github.com/keithah/bluescholars/actions/runs/39001990053) succeeded for `gh-pages` commit `f192c6bb67ba9b29f6071d85e39a92cca0f6bee7`; the Pages API reports `built` and serves [https://keithah.github.io/bluescholars/](https://keithah.github.io/bluescholars/).
- Live checks: 200 for `/`, `/2007/`, `/2009/`, `/2013/`, `/lj/`, `/archive-status/`, the SXSW and Word Count legacy articles, `/2013/blog/page/3/`, the recovered 2013 stylesheet, hero JPEG and original 2007 GIF; 404 for a missing route. Project-prefix assets and links load from GitHub Pages.
- The deployed 2013 page was visually inspected in the browser with its recovered styles, ribbon logo and front-page image. The 2007 and 2009 pages were inspected against the local project-prefix build. No screenshot file was saved. This is an agent-performed visual inspection; no human approval is claimed.
- The preview is not the release build. Remaining gaps and the full local checkpoint counts are in `docs/recovery-report/GAP_REPORT.json`; both review flags remain false.

- The final documentation-only `main` commit `451caccb671c4b819d9792bb070fd52e11fb2a6e` passed validation run [39002061515](https://github.com/keithah/bluescholars/actions/runs/39002061515), including unit tests and root/project-subpath builds.


## Post-deployment acquisition update — October 17, 2026

A second local 200-URL pass recovered 11 additional host-page records and five former placeholder routes, without adding unique bytes. The local root and `/bluescholars/` candidate check both passed after rebuild (955 recovered pages; 2,352 placeholders). The new 2009 capture routes have not yet been live-checked in this deployment snapshot; verify them after refreshing Pages. The previous public candidate commit remains `f192c6bb` until that refresh succeeds.


## October 17 final local candidate check before preview refresh

- Added regression `test_missing_social_share_icons_are_compact_without_hiding_article_photo_gaps`: it failed before the renderer change and now passes. `PYTHONPATH=. .venv311/bin/pytest -q`: **141 passed**. Compileall, shell syntax, `actionlint`, and `git diff --check` passed.
- Root and `/bluescholars/` candidate builds each report 955 recovered pages, 2,352 placeholders, four derived LJ views and 750 local assets; both checks return zero errors. A scan of 3,312 generated HTML documents plus local CSS found no automatic external asset URLs.
- Exact CDX for the PHOTOS: TONE lead image returned zero rows and the dated replay returned 404. The page keeps a named photo gap; only the small missing social-share icon labels were compacted. This does not add a source image or imply fidelity where the photograph is unavailable. The candidate is rebuilt locally but awaits the next Pages deploy.

## 206Proof preview refresh and next recovery batch — October 19, 2026

- Refreshed the existing unreviewed Pages preview as a fast-forward commit on `gh-pages`: `a21d4fad` (`Refresh preview with 206Proof forum editions`), parent `47875e8e`. No history was rewritten. GitHub Pages deployment [39296880964](https://github.com/keithah/bluescholars/actions/runs/39296880964) completed successfully; the Pages API reports `built`.
- Live HTTPS checks returned 200 for the homepage, `/206proof/`, `/206proof/2007/site/`, `/206proof/vanilla/forum/`, `/206proof/community/`, and `/206proof/vbulletin/4um/`. No screenshot file was saved. This is agent-run route verification, not owner visual approval.
- The deployed candidate contains 240 2007 Vanilla pages, 1,351 2008–2012 Vanilla pages, 642 community pages, and 77 vBulletin pages. The public snapshot predates the next local recovery batch.
- Continued recovery locally with another 160 Vanilla routes. The manifest now has 3,499 attempts (3,490 validated payloads, nine failures), including 2,590 HTML pages, 802 images, 91 CSS files, and seven validated MP3s. The refreshed media scan has 462 source-linked leads; only the seven MP3 files are recovered audio.
- Rebuilt the local candidate from those sources: 240 / 1,511 / 642 / 77 pages by era, 4,244 linked gap pages. `.venv311/bin/python -m pytest -q` passed (228 tests); the integrated `/bluescholars/` candidate offline check passed with zero errors. There are 3,617 selected Vanilla URLs left unattempted. The local batch is not included in the public Pages snapshot.
- Final-release flags remain false. The exact 2007 theme CSS is still missing, the many gap pages remain explicit, and third-party redistribution rights and owner visual review are still unresolved.

## October 20, 2026 — LiveJournal asset and root-path verification

- `.venv311/bin/python -m pytest -q`: **259 passed**. Python compileall, both shell-script syntax checks, `actionlint .github/workflows/pages.yml`, and `git diff --check` passed before this final documentation refresh.
- Rebuilt the reviewed-source project site at `/bluescholars/`: 1,049 recovered pages, 12 recovered feed pages, 2,208 documented placeholders, one derived page, 1,505 local source assets, and 5,574 known source/media gaps. The project-path check returned `{ "ok": true, "errors": [] }`.
- Rebuilt the same sources at the domain root in a temporary hard-linked project copy (real paths, so source containment checks were preserved). It contains 1,049 recovered pages, 12 feed pages, 2,208 placeholders, one derived page, and 1,505 local assets; its root-path check also returned `{ "ok": true, "errors": [] }`. A symlink-only test copy was rejected by the builder’s path-safety check and was discarded; it was not a product-code failure.
- Browser inspection covered the updated archive hub, 2007 News at `/2007/news.html`, the root-mounted 206Proof edition hub and a recovered discussion thread, and the project-prefix LiveJournal page. The LiveJournal poster resolves to the local reviewed 400×433 image; page stylesheets and rendered images are local; its disabled-form explanation is visually hidden and remains accessible. No new screenshot file was saved in this pass; the earlier captured screenshots remain under `docs/recovery-report/screenshots/`.
- Current acquisition state: 12,642 resource URLs; 4,810 recovered, 5,350 queued, 2,382 failed/retryable, 96 requiring individual compatibility review, and four excluded. The merged index holds 77,085 capture rows; 2,581 unique payloads total 163,119,834 bytes. `source/catalog.json` contains 12,647 records. This does not mean the entire archive has been recovered.
- `.venv311/bin/python -m restore visual-review --visual-reviewed` now records the agent-performed review independently: `visual_reviewed: true`, `human_visual_reviewed: false`, and `publish_approved: false`. Release output remains gated. At the time of that earlier checkpoint, owner permission had not yet been confirmed. The owner confirmed it on October 20, 2026; see the later section below. No commit, push, Pages configuration change, or deployment was made from that checkpoint.


## Owner permission confirmation and refreshed candidate — October 20, 2026

- The owner confirmed permission to publicly redistribute the archived original material in conversation. `source/review.json` records that as an owner attestation; it does not assign a license to third-party works. Source/publication review remains incomplete and `publish_approved` remains false. A release-mode build was attempted and rejected by the documented approval guard. No push or redeployment occurred.
- A 75-resource recovery batch added six validated records and 6,000 capture rows. Latest main index: 12,822 resource URLs, 165,338 indexed captures, 4,981 recovered records (2,741 unique payloads / 171,623,580 bytes), 283 needing review, 4,898 queued, and 2,656 failed/retryable.
- Refreshed project candidate: 1,054 recovered pages including 12 feeds; 2,221 explicit placeholders; one derived page; 1,568 main-site assets. Root and `/bluescholars/` builds/checks both pass with zero errors. The candidate records thousands of missing assets/media and is not a complete restoration.
- `.venv311/bin/python -m pytest -q`: 262 passed on the previous complete run; targeted review tests after metadata update: 7 passed. Full suite is being rerun after this checkpoint update.

## October 27, 2026 — activity-scaled timelines

- Full suite: `.venv311/bin/python -m pytest -q` — **320 passed**. Python compileall, `node --check public/archive-timeline.js`, and `git diff --check` passed.
- Fresh candidate builds from the main recovery checkout at `/` and `/bluescholars/` each report 1,108 recovered pages, 12 feed-recovered pages, 2,173 placeholders, and 1,879 local source assets. The root checker and `/bluescholars/` checker both return `ok: true`, zero errors.
- Generated timeline inspection confirmed the landing page has no slider. Archive pages show page-count-scaled major homepage/edition circles and minor page-capture ticks; labels include counts. The Blue Scholars timeline has 3 major and 14 minor marks; Prometheus Brown Twitter 12 major / 1 minor; Mass Line forums 5 / 5; LiveJournal 5 / 1; press archive 20 / 1. Browser accessibility inspection confirmed markers and the key on the local `/bluescholars/2007/` page. No screenshot was saved and no human visual review is claimed.
- Candidate remains an unreviewed preview; `visual_fidelity_verified` and `publish_approved` remain false. Pages refresh and live route verification are recorded below after completion.
- Pushed source commit `721bce27957331ff81ecf04f7ccf9b17923630c9` to `main`. Pages commit `68dacf9282a26c185133a984ac3798fe38fac3ad` is a regular child of `0fd8e4b6249fc3e814a1a1c9599580f9c81349e3`, retained `.nojekyll`, and deleted zero files. Deployment run [40473653492](https://github.com/keithah/bluescholars/actions/runs/40473653492) succeeded; Pages API reports `built` at [https://keithah.github.io/bluescholars/](https://keithah.github.io/bluescholars/).
- Live HTTPS checks returned 200 for the landing page, `/2007/`, Prometheus Brown Twitter, Mass Line forums, LiveJournal, the press archive, and both timeline assets; an unknown route returned 404. Live `/2007/` has 17 count-labeled activity marks (3 major, 14 minor), and the landing page has no timeline. Chrome accessibility inspection confirmed live major/minor labels, page totals, and the timeline key. No screenshot or human review was produced; release approval and visual-fidelity flags remain false.
