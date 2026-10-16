# Verification record — October 16, 2026

## Automated checks

- `.venv311/bin/python -m pytest -q` — **118 passed** (including Arquivo.pt page-history/domain-CDX resume tests and recovery progress reporting).
- `.venv311/bin/python -m compileall -q restore tests` — passed.
- `bash -n scripts/*.sh` — passed.
- `git diff --check` on implementation, tests, and documentation — passed. Original archived HTML is preserved byte-for-byte, including its source whitespace, so the check excludes `source/raw/` and its original-HTML test fixture.
- `actionlint .github/workflows/*.yml` — passed.
- After adding explicit notices/bridges without copying pages across historical editions, the root and `/bluescholars/` candidate checks pass with zero local-link errors. The `/lj/` pages have no broken local links or automatic remote resources.
- Reviewed-source build/check at `/` — passed (57 recovered pages, 305 placeholders, 31 local source assets).
- Reviewed-source build/check at `/bluescholars/` — passed with the same counts and no remote automatic asset dependency.
- The checker verifies no broken local links or automatic remote resources. External navigation links, such as historical social profiles and video links, remain ordinary anchors.

The counts above describe the current unreviewed candidate and will change after the remaining era captures are merged. The remaining checked targets are `/2009/blog/tourdates/` (linked from two recovered WordPress pages) and `/2013/archive-query/27bed984677400b185e8/` (a Squarespace-era post links to the preserved 2010 WordPress attachment query). A candidate check does not satisfy the release gate.

## Repository and Pages

- GitHub CLI login: `keithah`; `repo` and `workflow` scopes are present.
- Target repository: public `keithah/bluescholars`, default branch `main`.
- GitHub Pages endpoint returned HTTP 404 on 2026-10-16; Pages remains disabled.
- No deployment has been attempted and no live URL is claimed.

## Visual review

The reviewed local `/2013/` page was opened alongside the May 29, 2021 archive capture earlier in this continuation. At desktop width, the ribbon logo, navigation, sidebar spacing, photograph crop, and main image position match; the vertical offset is accounted for by the Wayback toolbar height versus the local restoration notice. The project-subpath rendering was also opened in the browser; CSS, logo, and hero photograph loaded from the local preview. The homepage image and recovered ribbon logo both rendered. At 390×844, the local page collapsed the navigation to the original mobile “Menu” treatment and displayed the photograph within the viewport. The browser did not apply that viewport override to the separate archive tab, so a pixel-matched mobile screenshot comparison remains open.

The project-subpath page at `http://127.0.0.1:8080/bluescholars/2013/` rendered in the same browser with the same local image and navigation destinations under `/bluescholars/`. These are agent observations; no human review is claimed. The site-wide review is still incomplete: the 2007 edition remains an explicit no-page-bytes gap, and the 2009 landing page currently mixes a few recovered routes with many route-gap entries. No human review is claimed, so visual/publication flags stay false.

## Known limitations

- Recovery coverage is not exhaustive yet. See [the recovery report](recovery-report/RECOVERY_REPORT.md) and [the gap report](recovery-report/GAP_REPORT.md).
- The offline checker establishes local consistency, not full historical completeness or pixel fidelity.
- No original font binaries are bundled. Archived video players are represented as external links; no video files were recovered.


## LiveJournal archive preview

The root gateway now links to `/lj/`, separate from the three official website generations. The browser preview at `http://127.0.0.1:8083/lj/` and the project-path preview at `http://127.0.0.1:8084/bluescholars/lj/` each showed the eight capture routes; the individual 2007 post retained its text/comments and six local photos. A browser screenshot was visually inspected in-session but no screenshot file was saved. The custom stylesheet was recovered after this preview; its built output now serves it locally, while the LiveJournal platform CSS bundle remains missing and that preview did not verify the original design.


The October 2011 LiveJournal captures were checked in the browser at both root and project-prefix previews. The `/lj/` index lists all eight saved HTML capture routes with dates. The custom journal CSS is now local, while the separate LiveJournal platform bundle remains unavailable. Candidate generation/check passed independently for `/` and `/bluescholars/` (449 recovered pages, 769 placeholders, 419 local assets, zero link errors). This is technical verification, not a human visual approval or release sign-off.

A direct scan of the generated candidate HTML (`src`, `poster`, embedded data, and stylesheets) and CSS (`url()`) found zero automatic remote resource references. External web links remain ordinary clickable links.

The exact October and August LiveJournal custom stylesheet captures are byte-identical (7,343 bytes, SHA-256 `87560599e9fb5ddc5cdba0675164f3bd80324540d346fc6ae38c26878e2f34ce`). Builder recovery now excludes CSS assets from its HTML-page route loop and emits the custom stylesheet locally. The separate LiveJournal platform CSS URLs remain missing.
