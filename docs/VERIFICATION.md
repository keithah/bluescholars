# Verification record — October 15, 2026

## Automated checks

- `.venv311/bin/python -m pytest -q` — **105 passed** (including Arquivo.pt page-history/domain-CDX resume tests and recovery progress reporting).
- `.venv311/bin/python -m compileall -q restore tests` — passed.
- `bash -n scripts/*.sh` — passed.
- `git diff --check` on implementation, tests, and documentation — passed. Original archived HTML is preserved byte-for-byte, including its source whitespace, so the check excludes `source/raw/` and its original-HTML test fixture.
- `actionlint .github/workflows/*.yml` — passed.
- Candidate build at `/` — completed (411 recovered pages, 723 placeholders, 106 local source assets); link/resource check reports three unresolved local targets.
- Candidate build at `/bluescholars/` — completed with the same content counts; link/resource check reports the same three targets with the project prefix.
- The checker verifies no broken local links or automatic remote resources. External navigation links, such as historical social profiles and video links, remain ordinary anchors.

The counts above describe the current unreviewed candidate and will change after the remaining era captures are merged. The remaining checked targets are `/2009/blog/tourdates/` (linked from two recovered WordPress pages) and `/2013/archive-query/27bed984677400b185e8/` (a Squarespace-era post links to the preserved 2010 WordPress attachment query). A candidate check does not satisfy the release gate.

## Repository and Pages

- GitHub CLI login: `keithah`; `repo` and `workflow` scopes are present.
- Target repository: public `keithah/bluescholars`, default branch `main`.
- GitHub Pages endpoint returned HTTP 404 on 2026-10-16; Pages remains disabled.
- No deployment has been attempted and no live URL is claimed.

## Visual review

The reviewed local `/2013/` page was opened alongside the May 29, 2021 archive capture. At desktop width, the ribbon logo, navigation, sidebar spacing, photograph crop, and main image position match; the vertical offset is accounted for by the Wayback toolbar height versus the local restoration notice. The homepage image and recovered ribbon logo both rendered. At 390×844, the local page collapsed the navigation to the original mobile “Menu” treatment and displayed the photograph within the viewport. The browser did not apply that viewport override to the separate archive tab, so a pixel-matched mobile screenshot comparison remains open.

The project-subpath page at `http://127.0.0.1:8080/bluescholars/2013/` rendered in the same browser with the same local image and navigation destinations under `/bluescholars/`. These are agent observations; no human review is claimed. The site-wide review is still incomplete (including the two older editions and representative blog/section pages), so the visual and publication flags stay false.

## Known limitations

- Recovery coverage is not exhaustive yet. See [the recovery report](recovery-report/RECOVERY_REPORT.md) and [the gap report](recovery-report/GAP_REPORT.md).
- The offline checker establishes local consistency, not full historical completeness or pixel fidelity.
- No original font binaries are bundled. Archived video players are represented as external links; no video files were recovered.
