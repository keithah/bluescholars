# LiveJournal styling and capture recovery — October 28, 2026

## Restored styling

The saved LiveJournal documents contain malformed void-link markup. BeautifulSoup nests later stylesheet links beneath an earlier empty stylesheet link. The renderer previously destroyed that subtree while iterating, losing valid stylesheet references even though their CSS was already preserved. It now collects every descriptor before removing the malformed nodes. A fixture reduced from an actual saved capture reproduces the failure; the regression test failed before the fix and passes afterward. Scripts remain removed.

Thirteen unavailable/unapproved later URLs for the same journal theme, S2 layout ID 19020223, now use the preserved October 2011 theme through individually documented aliases. The later markup retains the same journal structure. Comparison with the saved 2025 stylesheet shows the same core layout, colors and typography; differences concern platform controls, ad rules and proxy image URLs. This is explicitly a historical fallback, not an exact download of those later versions. The missing 2010 theme is not assigned a later replacement. Exact saved platform stylesheets remain version-specific.

Forty-seven rendered LiveJournal pages gain preserved stylesheet references (see `stylesheet-gains.json`). Recovered original styling restores the journal columns, colors, typography and platform header. Missing small icons now retain their documented small geometry, accessible missing-image labels and visible question marks instead of becoming large diagnostic boxes. On phones, the journal columns reflow, the sidebar follows the article, and article text remains readable without whole-journal scaling. Desktop historical geometry is retained.

## Images and page captures

Twenty-one exact LiveJournal graphic URLs were downloaded, representing twelve image payloads. Several payloads already existed under other URLs; these are not all new unique images. The batch includes user markers, previous/next/share buttons, sidebar controls and the print logo. Source URLs, resolved dates and hashes are retained.

A previously downloaded November 4, 2023 standalone capture of “Official Blue Scholars LP Re-Release Tracklisting” is now individually approved and integrated, with its three exact November 2023 stylesheet captures. The post is dated January 23, 2005. Its normalized article text exactly matches the preserved 2018 thread capture (SHA-256 `94e715db17e0096bb09f8f410930b90269fef34e5d59c4eff3c68c894bcd292f`). This adds a dated page version, not a newly discovered article. Earlier copies remain preserved. The three stylesheet approvals apply only to their exact versioned URLs.

## Remaining gaps and discovery results

The October 2007 calendar exact index returned zero rows. The inspected calendar replay and two later exact theme replays returned 404s. The old account URL prefix `http://www.livejournal.com/users/bluescholars/` timed out twice (20-second and 40-second request limits); its index checkpoint remains incomplete and resumable. That timeout is not evidence that no captures exist. The shared cooldown stayed enabled; no 429 occurred in this batch.

Some original header artwork, fonts, images and historical pages remain missing. Neither the old theme fallback nor the saved CSS proves full visual fidelity. The site remains an unreviewed recovery preview; global visual-review and publication-approval flags are unchanged.

Batch provenance: `recovery/batches/2026-10-28-lj-styling/`. From the repository root, using the configured Python environment, resume the incomplete older URL lookup with:

```sh
python -m restore index --url http://www.livejournal.com/users/bluescholars/ --match prefix --max-pages 1 --delay 3 --timeout 40 --retries 1
```

Inspect any returned capture individually before acquisition and integration. Do not repeat the completed zero-row October calendar lookup unchanged.

## Verification

The full local suite passed 347 tests. Desktop and phone styling previews were inspected. At a 390px viewport the journal is unscaled, its article is 309px wide, and the document is 375px wide. Final whole-site root and `/bluescholars/` builds each passed with zero check errors. Browser verification confirmed one timeline, local styles/images, and 17 loaded images in the inspected desktop capture. The modern tracklisting capture renders its original content and one timeline. Different dated captures still reference different unavailable icon URLs.

Screenshots: [desktop](screenshots/2026-10-28-lj-styling/desktop.png), [mobile](screenshots/2026-10-28-lj-styling/mobile.png). Deployment is tracked by the subsequent GitHub Pages commit and run; these local checks do not constitute human visual approval.
