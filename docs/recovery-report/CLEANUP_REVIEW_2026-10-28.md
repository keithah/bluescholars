# Archive cleanup review — October 28, 2026

This is an engineering review of the recovery preview, not human visual approval or a claim that historical recovery is complete. Existing source provenance and release approval flags are preserved.

## Findings and repairs

- The last targeted Mass Line deployment omitted the final shared-navigation pass. Full builds now provide the deployment snapshot; verify the shared timeline on both Mass Line sections before publishing.
- Timeline activity counts inferred dates from arbitrary forum IDs and asset hashes. Counts now use explicit capture paths and source dates, excluding assets and redirect pages. Mass Line homepages use their actual capture year.
- Arrow keys could become stuck before a missing year. Keyboard navigation now steps through available activity years, including Home and End.
- Recovered Mass Line Latin-1 text was decoded as UTF-8. Decode original bytes using detected encoding, then emit consistent UTF-8 metadata.
- Disabled historical forms left orphan newsletter controls active. Those controls are now visibly disabled; no historical subscription is submitted.
- Mass Line fragment links were lost. Preserve local fragments and standalone anchors.
- Legacy PHP bookmarks previously downloaded HTML or became 404s. Emit canonical HTML pages plus directory-index redirects for eligible old PHP paths, without overwriting independently recovered directory pages.
- Preserve vetted source-link metadata through sanitization, then prefer exact existing local destinations for supported cross-archive links. Keep provenance links pointing to their sources.
- The fixed-width early sites, MySpace, Twitter, forums, and LiveJournal clipped severely on phones. Fit their original layout geometry to narrow viewports, retaining artwork and image-map coordinates, and restore original sizing on desktop. Keep LiveJournal platform chrome below the archive toolbar. Improve shared toolbar label wrapping and artist-page text wrapping.
- The checker incorrectly accepted shared assets outside the project hosting path. It now rejects those escapes, checks HTM pages and non-renderable HTML suffixes, and uses a streaming parser with cached target lookups.
- The previous CI run passed tests and both hosting checks but exceeded its one-hour job limit during upload. Separate root and project builds into independent jobs after tests.

## Verification

- Baseline: 321 tests passed. Final implementation: 332 tests passed.
- JavaScript syntax, Python compilation, workflow YAML parsing, and whitespace checks passed.
- Initial deployed-snapshot audit covered 27,732 HTML files. Full resource/link checker returned zero errors for that snapshot; the timeline omissions were detected separately.
- CodeRabbit review identified two edge cases (metadata stripping and alias collision), both repaired. The follow-up review completed with zero findings.
- Mobile browser checks at 390px covered all 14 archive entry pages. Corrected historical layouts fit the viewport; sparse-year keyboard navigation advances from 2018 to 2020. A regression test also verifies that resizing back to desktop restores original sizing.
- Full rebuilt root/project verification and final snapshot browser evidence are recorded below when complete.

## Remaining limits

Recovery gaps remain in the existing inventories and archive-status pages. A functioning local link does not establish that the historical page, image, or media collection is complete. Original source links remain available for provenance. No new crawl or acquisition is claimed by this cleanup.

## Final local snapshot evidence

- Complete candidate builds succeeded for root and `/bluescholars/` hosting (866 and 867 seconds before checking). The last mobile-only shared CSS/JavaScript changes were copied into both completed outputs with refreshed content-hash URLs; full checks were then rerun on both final outputs and exited successfully with zero errors.
- Final snapshot: 27,926 HTML files; zero duplicate timelines. All 268 Mass Line site content pages and 5,903 forum pages have the shared timeline; navigation redirects are intentionally undecorated.
- Deployment dry run: zero deletions. The 194 added HTML files are legacy bookmark compatibility redirects.
- Browser inspection of all 14 entry cards at 390px: one timeline per destination, no overflowing document wider than the viewport, and no failed image request among images with a source URL. Explicit missing-image notices are not recovered images and remain visible.
- Browser interactions verified forum board navigation, the Squarespace mobile menu, the old PHP bookmark redirect, correct 2009 Mass Line selection, and sparse-year keyboard navigation. The desktop WordPress layout retained its original 900px width without zoom. Root hosting showed 14 cards and no homepage timeline.
- Screenshots and mobile measurements: [evidence folder](screenshots/cleanup-2026-10-28/).
