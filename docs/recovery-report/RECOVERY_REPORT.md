# Blue Scholars historical recovery report

**Updated:** October 17, 2026. **Scope:** separate copies of the 2007, 2009/WordPress, and Squarespace-era sites, with the May 29, 2021 homepage as the Squarespace visual reference.

## Latest local checkpoint — October 17, 2026

The current resumable checkpoint contains 11,118 resource URLs and 23,238 indexed capture rows. It holds 2,291 verified raw files (147,533,392 bytes): 3,837 recovered resources, 72 held for review, 1,473 failed, and 5,736 queued. The completed local 2013 continuation recovered 118 valid in-era CSS responses from 201 selected URLs; 110 are classified recovered and eight later captures remain needs_review. Eighty-three URLs remain unresolved. It found no new article HTML or image bytes in this batch. Detailed capture provenance is in [GAP_REPORT.md](GAP_REPORT.md) and [era-2013-local-20261017-report.json](../../recovery/era-2013-local-20261017-report.json).

The candidate contains 976 recovered pages, 2,181 placeholders, four derived LiveJournal views, and 1,044 local assets. Both root and /bluescholars/ offline checks pass with zero errors. Newly recovered CSS revealed more missing embedded dependencies, so current gap counts increased to 8,293 missing embedded resources and 183 unbundled font references. These remain source gaps; no font binaries are published. The public GitHub Pages site remains an incomplete candidate, with publication approval false. The latest 2013 capture report and current resumable checkpoint are preserved locally; see [current-checkpoint.json](current-checkpoint.json).

## Evidence collected

### Internet Archive Wayback Machine

The saved domain CDX checkpoint is marked complete. Its acquisition report records 8,178 capture rows. After the 2007 batch import and subsequent source-linked LiveJournal, image, TIFF, and Common Crawl acquisitions, the current local checkpoint contains 4,893 resource records and 8,362 attached capture rows. Capture metadata is not equivalent to recovered response bodies. The original run's domain scan has raw CDX batches preserved locally under `recovery/index/`; those generated working files are excluded from Git. A complete capture index describes available snapshots; it does not mean their response bodies have been downloaded.

Before the targeted exact image-host queries were added, the state exposed these latest-200-OK selections per URL: 373 resources in the 2007 date range, 799 in the 2009-to-pre-Squarespace range, and 193 in the Squarespace range. They are selection counts, not acquisition success counts. Use the `capture-era` command or the updated recovery workflow to fetch each selected dated response while preserving variants.

The existing selected homepage body is genuine HTML from `20210529010817`. Its reference photograph is separately identified at `20210529010844`, 27 seconds later. This is preserved as a resource-specific same-crawl dependency. The selected homepage CSS and the 2020 section pages are also present in the recovered source set. A Shop response captured in 2020 is a provider error; the raw bytes and provenance remain in recovery metadata but are not treated as shop content.

### Common Crawl

The initial local all-collection index sweep found 128 published index endpoints but reached only 6; 122 requests failed from that machine. Those six returned 380 unique domain responses, all acquired as original WARC records with collection, filename, offset, length, digest, and content hash recorded. Many are WordPress-era pages from the 2016/2017 crawls. This is useful independent evidence but is **not** full Common Crawl coverage.

Two additional collection queries were saved as reproducible JSONL seeds in `recovery/seeds/commoncrawl/`:

- `CC-MAIN-2009-2010.jsonl`: 19 valid archived site pages were fetched, including blog/article, bio, release, tour, and store routes from the early WordPress site.
- `CC-MAIN-2023-40.jsonl`: 5 page bodies were recovered from 16 relevant rows. Three `robots.txt` rows were rejected as non-HTML; the archived Shop response was rejected as a provider error. A captured blog/homepage response supplies a late Squarespace-era comparison point.

Common Crawl uses independent snapshots; identical capture hashes are deduplicated in storage but source rows remain documented. These captures do not replace Wayback captures from the requested editions.

### Arquivo.pt

The Arquivo.pt root-history query returned 12 capture rows from 2017–2023, including three successful original HTML responses from April 2018, July 2018, and October 2019. A live domain CDX scan returned 35 rows; its bounded selector retrieved the 2019 homepage and blog listing plus the 2018 favicon (three valid bodies, no failures). The blog listing contains twenty visible post cards; all eighteen internal post links were queried through Arquivo.pt exact version history, which returned zero captures. The associated article pages are already present from Common Crawl. Domain index and acquisition details are in [OTHER_ARCHIVES.json](OTHER_ARCHIVES.json) and the checkpoint files.

### Other archive checks

The Library of Congress catalog returned zero exact-name/domain records, while its wildcard replay endpoint returned HTTP 403 from this environment. Archive-It public full-text search located a 2009 Blue Scholars Twitter profile capture and related third-party sources; the individual replay was viewed in the browser. Its documented global `/all` CDX endpoint returned HTTP 403. Archive.today's index revealed one January 2013 homepage capture, but snapshot retrieval hit a CAPTCHA/security response. Trove access was stopped at an Anubis anti-bot page; the UK Web Archive lookup redirected to an error page, and Ghostarchive's exact homepage query returned no archives. These are service/search outcomes, not archive-wide absence findings. See the detailed [independent archive report](OTHER_ARCHIVES.md).

## Current saved source collection

`source/catalog.json` contains 3,268 inventory records. It points to 97 unique content-addressed original files in `source/raw/` (about 11.5 MB): 126 source records reference HTML bytes, 28 reference CSS bytes, and 3 reference image bytes. Several records intentionally share the same physical file by hash. The catalog also retains queued, failed, and review-needed findings; those are not usable content.

The local recovery checkpoint currently records 4,960 resource URLs: 1,037 recovered, 14 review-needed, 192 failed, and 3,717 queued. It has 846 unique downloaded files (64,227,608 bytes) and 8,891 attached capture rows. The latest local refresh is in `current-checkpoint.json`; the checkpoint and raw response files are ignored by Git and must be preserved separately before changing machines. Recovery raw is local and ignored by Git. Arquivo.pt and Wayback additions remain outside the reviewed source collection unless individually reviewed and promoted.

## Current reconstruction and verification

A desktop browser comparison of the May 29, 2021 baseline and the September 30, 2023 Wayback homepage shows the same logo, navigation, hero photograph, crop, and layout. The later HTML is byte-identical to Common Crawl's September 27, 2023 capture. This is agent visual inspection, not human approval. The builder keeps separate `/2007/`, `/2009/`, and `/2013/` editions, plus a separately hosted `/lj/` LiveJournal archive. Candidate counts are 449 recovered pages, 4 derived pages, 765 placeholders, and 420 source assets. Previously unresolved WordPress and cross-era links now have an explicit gap notice or a bridge to the recovered page in its original edition. The root and `/bluescholars/` candidate link checks pass with zero errors. Four LiveJournal post routes now render exact entry blocks from the October front-page capture as derived reading views; they are not counted as standalone recoveries. The eight recovered LiveJournal capture routes and 20 historically dated photos live in the ignored local recovery checkpoint, not the reviewed catalog. The reviewed-source build/check passes at root and `/bluescholars/` (57 recovered pages, 305 placeholders, 31 assets, zero automatic remote dependencies), but it remains incomplete and is not release approval.

The automated suite has 119 passing tests (including the new conservative recovery-artifact merge regression tests). At the owner’s direct request, the unreviewed candidate snapshot is published as a Pages preview at `https://keithah.github.io/bluescholars/` from `gh-pages`; it is not the final restoration release. `source/review.json` still has `visual_reviewed: false` and `publish_approved: false`.

## Resume commands

Locally, with working Internet Archive access:

```bash
python -m restore index --max-pages 20
python -m restore index-assets --max-assets 100 --max-pages 3
python -m restore recover --max-files 500 --retry-failed
python -m restore capture-era --era 2007 --max-files 2000
python -m restore capture-era --era 2009 --max-files 2000
python -m restore capture-era --era 2013 --max-files 2000
python -m restore commoncrawl --max-records 1800 --workers 4
python -m restore arquivo --history-url bluescholars.com
```

The manually dispatched GitHub Action is the current fallback for Wayback access. Run `38834520393` preserved the 2007-era retrieval artifact (368 of 373 selected resources recovered) but ended when candidate build hit a dated image-variant key bug; that builder defect is now fixed and covered by a regression test, but the workflow has not yet been rerun with the fix. Run `38824767784` ended cancelled at the 90-minute job ceiling; its artifact was imported locally. The smaller continuation `38834361363` failed before processing because artifact extraction collided with tracked report files; the resume workflow has since been corrected. Resume its last saved `archive-recovery` artifact by passing its numeric run ID as `resume_run`; choose one `edition_era` per run. Download the resulting artifact into staging, inspect the checkpoint and raw files, then merge it without replacing newer local work. The workflow is retrieval-only and does not publish.


### Separate LiveJournal archive

A source-linked LiveJournal journal was recovered from Wayback and Common Crawl. The `/lj/` section uses the latest old-layout captures from October 2, 2011 for its front page and two individual 2007 posts. Earlier January 2009 and August 2011 page variants are retained under dated capture routes, alongside a 2010 Common Crawl root response and a 2009 Common Crawl profile. The 2011 index includes six complete visible 2007–2008 entry texts; only two have standalone post captures. Twenty 2007–2008 photos are locally mapped. The custom LiveJournal stylesheet is recovered; exact platform CSS history queries returned no successful framework bundles, the later Eventful poster is withheld pending date review, and one Massline Media image resolves only to a Wayback lander. This separate host is not counted as one of the three official website generations; see [independent archive findings](OTHER_ARCHIVES.md).

## Latest recovery checkpoint — October 16, 2026

The local merged recovery checkpoint now contains 8,838 resource URLs and 9,210 attached capture records: 2,908 recovered, 50 needs review, 1,120 failed, and 4,760 queued. It stores 1,969 unique downloaded files totaling 107,780,030 bytes. This is resumable local recovery material; it is not all in the reviewed source catalog.

Broad Wayback run [38962246474](https://github.com/keithah/bluescholars/actions/runs/38962246474) reached the 90-minute acquisition cap. Its candidate build/check and artifact upload succeeded. Merge added 61 index batches, 23 resource records, 144 dated variants, and three raw files without conflicts. Common Crawl run [38972843891](https://github.com/keithah/bluescholars/actions/runs/38972843891) queried a bounded sample, attempted 28 WARC records, and recovered 27; merge added 68 resource records and five unique raw files, with 1,748 duplicate file hashes and no conflicts. Arquivo.pt yielded no new bodies on that pass. A new 2,000-resource Wayback continuation [38975520061](https://github.com/keithah/bluescholars/actions/runs/38975520061) is active from the Common Crawl checkpoint.

The merged offline candidate now builds to 924 recovered pages, 1,878 placeholders, four derived LiveJournal reading views, and 729 local source assets. The candidate checks pass at `/` and `/bluescholars/` with zero local-link errors. Remaining measured gaps include 4,045 embedded assets, 295 linked assets not recovered, 145 external media links, 17 fonts, and nine invalid source records. Automatic rendering references remain local under the candidate Content Security Policy; external archive/source URLs appear as ordinary links. This does not establish complete content or visual fidelity. Human visual review and publication approvals remain false, so the Pages branch has not been redeployed.

Search-engine discovery also found dated third-party leads for the 2007 Jamglue contest and the 2009 OOF! release post; see [OTHER_ARCHIVES.md](OTHER_ARCHIVES.md). These are corroborating sources, not original-site captures.

## October 17, 2026 continuation

The broad Wayback continuation [run 38975520061](https://github.com/keithah/bluescholars/actions/runs/38975520061) reached the 90-minute acquisition cap. Its recovery artifact, candidate build, and artifact upload succeeded. Merging that artifact added 81 resource records, 33 dated capture variants, 86 index batches, and three unique raw files; 1,753 file hashes were duplicates and there were no conflicts. The consolidated local checkpoint now has 8,952 resource URLs, 9,271 indexed capture rows, 3,032 recovered resources, 50 held for review, 1,193 failed attempts, and 4,677 queued. Its 1,972 unique raw files total 108,454,143 bytes. These counts include URLs and assets as well as pages.

The latest unreviewed candidate built from that checkpoint contains 924 recovered pages, 1,851 marked placeholders, four derived LiveJournal reading views, and 732 local source assets. The offline checker passed at both the domain root and `/bluescholars/` with zero broken local targets, unsafe links, or remote automatic resources. Build findings remain 4,110 missing embedded assets, 295 linked assets not recovered, 145 media links without local media, 18 fonts not packaged, and nine invalid source records. These are source gaps, not passing completeness claims. The release and visual-fidelity flags remain false.

A resumed broad Wayback batch, [run 38985105267](https://github.com/keithah/bluescholars/actions/runs/38985105267), is active from the merged checkpoint. It is configured for up to 2,000 files per run and continues from its prior artifact; after each completion, merge the artifact before queuing the next batch. Current local counts are also recorded in `current-checkpoint.json` and `GAP_REPORT.json`.

### Source-linked post and capture comparison

A citation in the [Cinemetropolis article on Wikipedia](https://en.wikipedia.org/wiki/Cinemetropolis#References) pointed to a [May 20, 2011 Wayback capture](https://web.archive.org/web/20110520234313/http://bluescholars.com/blog/update-cinemetropolis-advance-digital-download-out-now-official-release-date-june-14/) of the May 17 post “UPDATE: CINEMETROPOLIS Advance Digital Download Out Now, Official Release Date June 14.” The citation led to a real archive capture, not a reconstructed title. Its raw bytes were already present in the local recovery checkpoint (14,191 bytes; SHA-256 `584a3828d3b5afc1f420f46404ef1bb8a8b0d573191c675718ac6870bcb6c3ce`) and the article is available at `/2009/blog/update-cinemetropolis-advance-digital-download-out-now-official-release-date-june-14/` in the preview.

The May 2011 `/blog/` capture contains seven visible comments. The July 2011 capture of the same route has eleven and remains the default local page because it is a later compatible copy. Two 2012 captures preserve the same post under a no-`/blog/` URL and include an added contest navigation item; they remain separate routes in the 2009 WordPress edition. The May 22 print view is also kept as its own source route. Hashes, source URLs, and individual compatibility decisions are in `capture-compatibility.json`. No alternate is blended into the May 29, 2021 Squarespace edition.

An older Squarespace listing was also retrieved from the June 11, 2016 capture after individually inspecting the 2019 replay (a Wayback provider error). The 2016 HTML contains 20 entries from January 12, 2013 through November 13, 2012; these are inventoried as B41–B60 with observed permalink slugs. The 20 listing entries point to 18 distinct article routes; all 18 have locally recovered pages from individual Wayback or Common Crawl captures, separately from the listing body. Raw source: `recovery/raw/8dc84128b2368456b9bbe1f8d107acbee3a2f89e8511353ea1bbaff323f27fda.html` (SHA-256 `8dc84128b2368456b9bbe1f8d107acbee3a2f89e8511353ea1bbaff323f27fda`).

An exact Wayback CDX pass for the 18 post routes linked by the 2016 listing returned one 200 HTML row for every route. Eleven rows match the capture already used. Seven routes have a distinct 2019 row (about 824–836 bytes); individual replay attempts showed three captured provider-error pages and four transport failures, so the latter remain unknown rather than classified as missing. The per-route CDX rows and attempt outcomes are in [post-route-cdx-2026-10-17.json](post-route-cdx-2026-10-17.json).

Four source-linked Squarespace CSS parts from the 2016 template were retrieved individually and are now packaged locally: P35-P38, captures 20160624015144, 20160624020908, 20160624014732, and 20160624015113 (581,080 bytes total). Their styles load from local paths in the GitHub Pages project-prefix build. The Squarespace UI WOFF font was subsequently recovered from an exact 2013 capture and is retained in local recovery provenance; the current candidate omits font binaries under the no-redistribution policy; the social icon font still has only HTML-landed Wayback responses. Twenty image IDs observed on the older listing were tested across two dates (40 replay attempts); none yielded a valid image payload, so those photos remain gaps.

The 2016 stylesheet also references `squarespace-ui-font.woff`. The exact HTTPS URL has 57 Wayback `application/octet-stream` 200 rows with stable digest `BVAWN6UNBT4AATQKQJGQTFGUJ62IR3VN`; capture `20130926135509` yielded a valid 9,068-byte WOFF (P39, SHA-256 `b980267ac2254ef534bfe32055489ed677d461077b37f2ee62bf7b5fc4f7362f`). The raw response stays in the ignored recovery checkpoint; public output omits it and uses CSS system fallbacks. The social icon WOFF remains unrecovered.


## Additional Squarespace listing captures — October 17, 2026

Two individually inspected listing pages were recovered: the reverse-pagination capture `20160611091915` (20 observations, September–February 2013) and author-filtered capture `20160529163313` (20 observations, February–January 2013). They add B61–B100. Across both, 37 distinct internal post routes are linked; all 37 have independently recovered page bytes, including 33 routes newly added to the source manifest. Three entries link to third-party pages and are not represented as Blue Scholars captures.

The page-two URL history was also inspected individually: eight CDX rows across slash/no-slash spellings and captures from 2015 through 2023. Seven captures through 2020 have the same normalized 20-entry article-text signature; the 2023 capture contains a different entry set and remains held as a later alternative. The default candidate continues to use the 2020 capture. Raw variants, hashes, sizes, and exact CDX URLs are recorded under P07 `capture_variants` and Q58–Q61.


## Current measured checkpoint — October 17, 2026 (after listing inventory and font-policy update)

The complete local Wayback index has 21,517 capture rows across 9,092 resource URLs. The checkpoint contains 1,983 unique raw files (110,018,036 bytes): 3,045 recovered resources, 50 held for review, 1,193 failed, and 4,804 queued. Capture availability and downloaded response bodies are separate counts.

The candidate has 924 recovered pages, 4 derived LJ views, 1851 placeholders, and 737 local source assets. Root and `/bluescholars/` offline checks both pass with zero errors and zero remote automatic resources. Current findings include 5,724 missing embedded assets, 295 linked assets not recovered, 145 external media links, 22 font resources not bundled, and 9 invalid source records. All recovered font binaries are withheld from public output; CSS declarations fall back to system fonts.

The source manifest contains 237 records and 236 blog-entry observations. Beyond the five general lists (B01–B100), 36 recovered tag/author listing captures yielded 136 additional observations and 46 newly inventoried post bodies, each backed by its own recovered response. See the manifest and checklist for timestamps, hashes, and source URLs. The public site is an unreviewed preview; both review flags remain false. Wayback continuation `38985105267` was still in progress at the last status check.

## Public preview refresh — October 17, 2026

GitHub Pages build `38990662133` succeeded for `gh-pages` commit `efad4d3e2a2fefefcb78b7d29761d474857d86cd`. The verified URL is [https://keithah.github.io/bluescholars/](https://keithah.github.io/bluescholars/). HTTPS checks returned 200 for the homepage, `/2007/`, `/2009/`, a newly inventoried 2013 article, and `/2013/blog/page/3/`; an unknown route and the withheld WOFF URL return 404. The browser showed the edition cards and the recovered post content with no console errors. This is an unreviewed candidate preview; `source/review.json` remains false. The browser screenshot was captured for agent inspection but not saved as a local image file.


The October 17, 2026 local 2009 continuation attempted 98 eligible URLs from the newer checkpoint and validated 21 responses: five HTML, four CSS, and 12 images. One additional route now renders in the 2009 edition; eight unique raw files (21,472 bytes) were added, and the rebuilt candidate lists 1,055 local source assets; 77 URLs remain unresolved, mostly feeds and invalid replay responses. See `recovery/era-2009-local-20261017-report.json` for every timestamp, source URL, digest and failure. The candidate now has 501 recovered 2009 pages (977 recovered pages total), and both deployment-path offline checks pass.


A later broad 200-URL retry validated two additional 2009-era HTML captures, both duplicate payload hashes already in the raw corpus: the `/blog/category/the-music/` capture resolved to `2010-02-17`, and `/blog/n30-a-personal-history-by-geo/` resolved to `2011-03-12`. It added no bytes or rendered routes. Root and project-subpath candidate checks still pass. See `recovery/broad-200-local-20261017-report.json`.


A second 200-URL retry validated nine 2009-era HTML responses, including the City Arts Fest listing, “7 Questions with Bambu,” the SXSW 2009 listing, “News: We Have a Winner,” and “Bayani Redux Dropping September 1.” It added two inventory URLs, eight CDX rows, and one unique 10,490-byte payload; candidate route counts remained 977 recovered pages. See `recovery/broad-200-local-20261017-second-report.json` for full provenance.


The third broad retry validated ten additional WordPress HTML capture responses from 2009–2011, adding one URL and one CDX row. All ten payloads were already in the corpus. Candidate route totals remained 977 recovered pages, with root and project-subpath checks passing; the complete attempt log is in `recovery/broad-200-local-20261017-third-report.json`.


The fourth broad retry validated ten HTML responses, adding the Seattle 100 post and one unique 26,243-byte capture. The fifth validated eleven HTML responses, including the Seattle police coverage entry and five Cinemetropolis listening-party photo entries; it added one URL and 13 index rows. These results updated existing 2009 routes without increasing the candidate’s route count. Both roots pass offline checks. The reports `recovery/broad-200-local-20261017-04-report.json` and `recovery/broad-200-local-20261017-05-report.json` preserve all dates, URLs, sizes, and hashes.


The sixth broad retry validated nine 2009-era HTML responses and added 12 newly discovered URLs, five CDX rows, and one unique 25,793-byte payload. Twelve archive-query outputs were refreshed with source-backed material; the site still has 977 recovered page routes. Root and project-subpath checks pass. The capture-by-capture report is `recovery/broad-200-local-20261017-06-report.json`.


The eighth broad retry validated four HTML bodies while adding 21 URLs and six CDX rows. The captures are dated variants of the Sade remix, MLK workshop and Cinemetropolis routes; no unique raw files were added. It reduced placeholders to 2,179 and moved the LP attachment page into the 2009 edition. Root and project-prefix checks pass; see `recovery/broad-200-local-20261017-08-report.json`.


The seventh broad retry processed 200 URLs, validated eight HTML responses, added 11 resource URLs and 13 index rows, and saved three previously unseen bodies totaling 78,504 bytes. It changed nine 2009 archive-query views. Per-capture provenance is preserved in `recovery/state.json`; the batch totals are recorded in [the seventh retry report](../../recovery/broad-200-local-20261017-07-report.json).


A tenth broad retry validated 9 HTML capture responses from 200 URLs. It added seven resource URLs, 38 index rows, and three previously unseen raw bodies totaling 35,479 bytes. The new source updated the Jean Quan and Paramount photo entries and restored edition-specific bio/store pages; one recovered route was added overall, leaving 978 recovered pages and 2,176 placeholders. Both root and `/bluescholars/` checks pass. Capture timestamps, hashes and source URLs are in [the tenth retry report](../../recovery/broad-200-local-20261017-10-report.json).


An eleventh broad retry validated 16 HTML captures from 200 URLs, adding 24 resource URLs, 83 index rows, and seven unique raw bodies totaling 54,644 bytes. Root and `/bluescholars/` candidate checks both pass; the build now contains 981 recovered pages and 2,176 placeholders. New material updates the 2007 static pages and 2013-era news/events/press pages. Some newly linked source pages resolve to 2004/2005 capture dates; those dates are preserved rather than relabeled as 2007. Capture-by-capture URLs and hashes are in [the eleventh retry report](../../recovery/broad-200-local-20261017-11-report.json).


Eleventh-batch preview deployment: `gh-pages` commit `dac1edae56555ad01cede24424bcdcb0ab13328e` was built successfully by [Pages workflow 39059635467](https://github.com/keithah/bluescholars/actions/runs/39059635467). The public hub, new 2007 static pages, 2009 and 2013 archive-query views, edition roots, LJ, recovery status, and local CSS return HTTP 200; an unknown route returns 404. A scan of generated HTML and CSS found zero remote automatic assets. This remains an unreviewed candidate preview, with publication approval false.


A twelfth broad retry validated 27 HTML responses and expanded the archive index by 1,224 rows, adding 34 URL records and 14 unique raw bodies totaling 166,906 bytes. The build remains at 981 recovered pages with 2,177 placeholders; both root and `/bluescholars/` checks pass. The refresh updates older static-page and 2013-era page variants and the status report, while several prior paths leave the route map. Exact source URLs, requested/resolved timestamps and digests are in [the twelfth retry report](../../recovery/broad-200-local-20261017-12-report.json).


Twelfth-batch preview deployment: `gh-pages` commit `7fd81a7771522fceb61b3e6190e6d8e544f18b97` was built successfully by [Pages workflow 39060634246](https://github.com/keithah/bluescholars/actions/runs/39060634246). Live checks returned 200 for the refreshed 2007 pages, the 2013-era static routes, both generated archive-query destinations, LJ, archive status and local CSS; an unknown route returned 404. The Pages API reports `built`, HTTPS is enforced, and a scan of generated HTML/CSS found zero remote automatic asset references. The site remains an incomplete unreviewed candidate, not an approved final release.


A thirteenth broad retry validated 32 responses (31 HTML, one CSS), expanded the capture index by 1,338 rows, and added 67 URLs plus 12 unique raw bodies totaling 292,111 bytes. The candidate now lists 985 recovered pages and 2,185 placeholders. Both deployment paths pass; the refreshed preview is live at [`gh-pages` commit 3cbf190](https://github.com/keithah/bluescholars/actions/runs/39061790395), with zero automatic remote assets. The batch includes a dated Squarespace CSS response, preserved with its source digest, but the local asset count did not increase. Two responses remain under `needs_review`. See [the thirteenth retry report](../../recovery/broad-200-local-20261017-13-report.json).

## October 21, 2026 — Wayback media continuation

Two bounded passes of 50 eligible resources each expanded the index by 59 CDX rows and one URL. Together they resolved 31 capture records: 21 in the first pass and ten more image URLs in the second. The first pass included six new content hashes (117,058 bytes); the second pass returned ten hashes already represented by alternate host aliases, expanding provenance without increasing unique bytes. All 16 resolved image URLs were individually hash-checked and added to the source inventory with their original URL, Wayback capture timestamp and referrer context: two 2006 navigation GIFs, three video thumbnails captured in 2012/2015 from URLs linked by the archived video page, and a 2008 band photo linked by the legacy blog. The last image is identified with its archived source host (`ill-literacy.com`); its archival inclusion is not a claim of copyright ownership.

Checkpoint totals after both batches: 13,053 resource URLs, 185,655 indexed capture records, 5,375 recovered, 301 needs review, 4,496 queued, 2,877 failed, four excluded, 2,818 unique downloaded files (174,976,958 bytes), and 13,477 failed attempts. These are cumulative inventory/status totals. The source collection changed, so existing candidate builds do not include these files; rebuild and run both deployment-path checks. Publication approval and visual review remain false.
