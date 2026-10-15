# Recovery gap report

**Updated:** October 15, 2026. This report distinguishes a checked limitation from a search still in progress. Network failures and unqueried URLs are not evidence that a resource is absent from every archive.

## Checked limitations

- The 2020 `/shop` capture at `20200718164929` is a captured provider-error page, not the original shop. Keep it out of the rendered content until another valid shop capture is recovered.
- Eleven YouTube embed IDs survive in the handoff inventory, but no video binaries were recovered. The restored pages can preserve the links and observed order; playback is not part of the local static copy.
- Font binaries are excluded by the repository policy, so original declared font families may fall back to system fonts.
- Current reviewed source bytes include only three images. The current candidate emits 27 local static assets after including CSS and generated assets; many observed gallery, blog, and legacy-site images remain unavailable locally.
- The Common Crawl all-collection endpoint sweep had 122 of 128 index queries fail locally. Six collections yielded 380 site responses. Separate targeted 2009–2010 and 2023–40 samples added material, but no complete Common Crawl sweep has passed.
- The first Squarespace-era root located in Wayback is September 21, 2013; the last intact homepage capture observed so far is September 30, 2023. The 2024 domain capture is post-takeover material and is excluded from the historical Squarespace edition.

## Still being searched

- **2007:** the CDX inventory contains 2007 homepage captures, including July 24, 2007, but no 2007 page body has been saved in the current source collection. Obtain the latest valid 2007 root and linked pages from Wayback; inspect the alternate 2007 captures individually. The older site is not visually restored yet.
- **2009 / WordPress:** the independent Common Crawl sample yields early WordPress article/site pages, but per-URL Wayback captures across 2009–September 2013 remain to be fetched and compared. Many article image URLs and legacy navigation paths remain queued.
- **Squarespace:** fetch every URL's final usable capture within September 2013–September 30, 2023, then inspect articles, both blog listings, shows, Holler, video, shop variants, and source-linked media. The domain index includes many pages that have not yet yielded source bodies.
- **External images:** the 42 image URLs from the expanded source inventory need exact-URL archive indexing and dated retrieval. The current recovery workflow now performs these targeted index requests; it has not completed those new runs yet. Blog images discovered outside those 42 seeds also need exact, source-backed searches.
- **Blog completeness:** the inventory contains 40 observed listing entries, not a verified lifetime post count. The full set of post permalinks, offsets, author/tag listings, captions, source credits, and attached images is not yet confirmed. Do not infer missing slugs or claim every post has been recovered.
- **Original typography:** no font binaries are bundled. A local visual comparison is still needed to measure the resulting fallback difference.

## Release blockers

1. Complete and merge the resumable 2007, 2009, and 2013 capture runs, plus source-linked image and independent-archive recovery.
2. Rebuild the gap report from the final checkpoint and inspect each newly promoted source for date compatibility, provider errors, and content correctness.
3. Record desktop and mobile comparison evidence for the May 2021 baseline, the two older editions, representative articles, and section pages. Do not claim human review unless a human has performed it.
4. Pass the reviewed-source release build and root/project-subpath checks with no remote automatic asset dependency.
5. Keep `source/review.json` false until the visual and publication decisions are properly recorded. Then, and only then, enable Pages and verify the deployed root, nested content, assets, pagination, and 404 behavior.

## Safe continuation

Read [the recovery report](RECOVERY_REPORT.md) and [the work log](../WORK_LOG.md), check the latest `archive-recovery` run under `keithah/bluescholars`, and resume using that artifact's run ID. Keep acquisition, candidate output, promoted source bytes, and release output separate. No history rewrite or DNS change is needed.
