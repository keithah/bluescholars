# Common Crawl page recovery and spam-filter correction — November 1, 2026

This pass looked for pages missing from every site area: bluescholars.com, LiveJournal, Prometheus Brown, Sabzi, Mass Line Media/forums and MySpace. It recovered **72 previously unrecovered HTML pages** from Common Crawl, recovered 13 more Blue Scholars images from Wayback, and corrected a spam filter that was rejecting genuine pages.

## Recovered pages

All bodies were fetched as byte-range WARC records from `data.commoncrawl.org`. Each record keeps its collection, WARC file, offset, length, CDX digest, capture timestamp, SHA-256 and byte count.

- **bluescholars.com: 34 pages** from `CC-MAIN-2013-20`, captured May 19 to June 20, 2013. They include 2010–2011 posts such as "Jean Quan: From Cal Activist to Mayor of Oakland", "Grynch: A Reintroduction by Geo", "TOUR BLOG: DAY 1 – POMONA, CA", "7 Questions with Gordon Voidwell", the Stüssy "TOWN ALL DAY" release and three of its attachment pages, plus the Press, Contests, Uncategorized and Upcoming archive pages and pages 12, 23, 24, 60 and 73 of the post index. Before this pass, 11 of these URLs were marked failed in the Wayback state, because every Wayback capture failed full-HTML validation. Another 15 were queued, and 8 were not in the inventory. They are added to the local resumable state (`recovery/state.json`, which is not in Git), and the Wayback captures and attempts for each URL are kept. The 34 bodies are in the local `recovery/raw/` cache. Their WARC coordinates in `cc-warc-fetch.json` let anyone fetch them again.
- **Prometheus Brown: 38 blog pages** from `CC-MAIN-2009-2010`. 37 pages captured September 3, 2010 were added to the 2010 WordPress edition (homepage capture 20100925). The July 5, 2009 capture of "Battle in Seattle" was added to the 2009 edition. Each page is added only to an edition whose homepage capture is on or after the page's capture date. The pages include film reviews (Hanyo, Objectified, Humpday, Crimson Gold, Oktyabr, The Murder of Fred Hampton), the "Resistance of Philippine Cinema" and Rik Cordero interview essays, the 2008 top-10 list, monthly archives and video posts. Nine of them fill pages that were previously listed as edition gaps. The bodies are tracked in `recovery/artist-sites/raw/`, with `source_archive: "Common Crawl"` in the manifest.

The March 2010 copies of 14 Prometheus Brown pages in `CC-MAIN-2009-2010` are each exactly 523,945 bytes and have no closing `</html>`, so they were truncated during the crawl. They were fetched and recorded but not used. The complete September 2010 copies were used instead. The three `masslinemedia.com` rows in `CC-MAIN-2014-23` are the later German jewelry site and were not fetched.

## Spam-filter correction

The artist-site and Mass Line filters rejected any capture whose text contained the substring `cialis`. That substring also occurs in "socialist", "socialism" and Godard's *Socialisme*, which are common words on these political sites. Because of this, 14 genuine Prometheus Brown edition records were excluded as "spam-injected". These include "TRAILER: Socialisme", "AOKI: World Premiere", "Pacquiao-Cotto 24/7", "Humpday", "Objectified" and the 2010 contact page. Up to seven Mass Line forum replays were excluded the same way.

`restore/spam.py` now matches spam terms as whole words only. Both `artist_sites.py` and `massline.py` use it. `tests/test_spam_terms.py` covers both cases: genuine political vocabulary passes, and real injected pharmacy and casino spam (for example the 2009 "Cialis Get Viagra" capture) is still rejected. The affected Wayback captures are retryable with `--retry-failed`. The retry began, but the Internet Archive blocked this IP before it reached them (see below).

## Other areas checked

- **Mass Line forums:** 25 topics have no saved copy at all. Every Wayback capture of them, including `prev_next` and `msg` variants, is a 306–330-byte SMF database-error body. Wayback has nothing more for these topics. The two 2007 forum captures excluded by the old spam filter (a printpage view of topic 3335 and the showPosts page for profile u=77) can now be retried. The three 2009 `/smf/` captures excluded with them are likely real spam or parked pages and need inspection before use.
- **MySpace:** the two profile captures that failed with a gzip `ContentDecodingError` (20080707050101 and 20080724054056) could not be fetched raw, because the Internet Archive refused connections at the time.
- **Main site Wayback queue:** a pages-first pass tried the 18 queued bluescholars.com pages that still had status-200 Wayback rows, then recovered 7 of the 13 new images before it was stopped. 17 failed full-HTML validation on every indexed date, and 1 stays queued. None of these 18 is among the Common Crawl pages. 179 queued pages have no capture rows. They need exact-URL index queries, which were not reached.

## Archive service limits

The Internet Archive (`web.archive.org`) refused TCP connections twice during this pass, and `archive.org` stayed reachable. These were IP-level refusals, not HTTP 429 responses. The existing recovery code recorded each refusal as a failed capture. Those false failure records were removed. The extra runs in this pass treated a refused connection as a 30-minute cooldown, so the work stayed queued instead.

The Common Crawl index then started refusing connections as well. Of 645 collection/domain queries, 21 returned rows, 10 returned no rows, and 614 failed (HTTP 502/503/504, or connection refused). These failures are not evidence that the pages are absent. `cc-index-scan.json` keeps the outcome of every query, so a later run can query only the failed ones.

## Evidence

- `recovery/batches/2026-11-01-commoncrawl-pages/cc-index-scan.json` — every collection/domain query, with its outcome and returned rows.
- `recovery/batches/2026-11-01-commoncrawl-pages/cc-warc-fetch.json` — all 86 WARC records fetched, with completeness and old-filter flags.
- `recovery/batches/2026-11-01-commoncrawl-pages/cc-integrate-main.json` and `cc-integrate-artist.json` — the records that were integrated.

## Resume

When the services accept connections again, run one process at a time with slow pacing:

```sh
./.venv311/bin/python -m restore artist-recover --retry-failed --max-files 300 --delay 3
./.venv311/bin/python -m restore recover --host bluescholars.com --max-files 200 --delay 3
./.venv311/bin/python -m restore recover --host bluescholars.livejournal.com --max-files 60 --delay 3
```

Re-query the 614 failed Common Crawl collection/domain pairs listed in `cc-index-scan.json` one at a time. Recovered pages remain unreviewed candidate material, and the release-review flags are unchanged.

Run main-state recovery from the main checkout, not from a worktree that links to the shared `recovery/state.json`. `State.save()` writes a temporary file and renames it over the target, so the first save replaces the link with a separate copy. This pass hit that problem and copied its state back to the main checkout afterwards.

## Verification

All 356 tests pass. The `/bluescholars/` candidate build succeeded with 1,147 recovered Blue Scholars pages; the previous build had 1,108. The new pages render, for example `/2009/jean-quan-from-cal-activist-to-mayor-of-oakland/` and `/prometheusbrown/2010/blog/2009/01/free-hawaii/`. The offline check reported 5,354 errors, all under `206proof/`. They come from this worktree's environment: its ignored `recovery/206proof/raw/` has 4 of the 6,744 files present in the main checkout. They are not caused by this change, and no other area had check errors. No human visual review was done. `visual_fidelity_verified` and `publish_approved` remain false.

## Second pass — November 1, 2026 (evening)

The Internet Archive and the Common Crawl index accepted connections again at 18:18 UTC. This pass continued from the resume list above.

### Common Crawl without the index server

The Common Crawl index server (`index.commoncrawl.org`) soon refused this IP again. The 614 failed collection/domain queries were therefore answered from Common Crawl's raw index files on `data.commoncrawl.org`. `scripts/commoncrawl_cluster_scan.py` binary-searches each collection's `cluster.idx` with byte-range requests, then fetches only the compressed CDX blocks that can contain a domain. On two pairs the index API had already answered (`CC-MAIN-2009-2010|prometheusbrown.com`, 92 rows; `CC-MAIN-2013-20|bluescholars.com`, 78 rows), it returned the same rows.

All 614 pairs completed. The same method then queried every collection for five more keys: the hosting alias `02cd02a.netsolhost.com` and the MySpace profiles `bluescholars`, `prometheusbrown`, `sabzi` and `masslinemedia`. Of 1,290 collection/key queries, 368 returned rows and 922 returned none; none failed. Every outcome is in `cc-index-scan.json`.

Recovered from those rows (WARC records listed in `cc-warc-fetch-2.json`):

- **Sabzi: 97 pages** added to the 2019 Squarespace edition. These are the beat-tape pages (01RAVENNA through 09CINE, DELRIDGE, EXIT163A, MYTHICAL, PARTHENIA, PHO99, RAINIER, YESLER, the wøøds) and the blog posts, including the beat-tape download notes, "duplicate tracks on RAVENNA fixed!", SKRATCH and the Instagram posts. Captures are from September 2018 to February 2019, before the edition's October 2019 homepage. The latest complete capture of each page was used.
- **Prometheus Brown: 2 pages** (`index.html` and "The Resistance of Philippine Cinema", February 2017) added to the 2019 edition.
- **bluescholars.com: 4 pages** from `CC-MAIN-2012`: "NEW TRACK: Blue Scholars 'Summertime in the SEA'", post-index pages 15 and 69, and one Loft Honolulu photoset attachment page. Two of them were previously marked failed in the Wayback state.
- **LiveJournal: 1 comment thread** (`16015.html?thread=49807`, 2017), previously failed in Wayback.
- **MySpace: 15 profile revisions** (bluescholars ×10, masslinemedia ×3, sabzi ×2; 2008–2013), added to `recovery/wayback-versions/manifest.json` with `source_archive: "Common Crawl"`. 8 are complete. The two July 2008 bluescholars records carry the same content digests as the two Wayback captures that failed gzip decoding. Common Crawl stored them truncated at 131,073 bytes, so they are flagged `complete_html: false` and cross-referenced from the failure records.

Not used:
- 8 Prometheus Brown 2008 post URLs captured in April 2020: each is a provider error page.
- `masslinemedia.com/smf/` topics 132 and 517 (2016–2017): each is a 1,556-byte JavaScript cookie check, not a forum page.
- The later German jewelry pages on `masslinemedia.com`, and a 2026 parked `sabzi.co/lander` page.
- The hosting-alias rows were all already recovered.

### Wayback

- **Prometheus Brown: 40 pages and 3 images** (`wayback-artist-retry.json`). With the whole-word spam filter, all ten 2009 pages wrongly excluded before were recovered: "TRAILER: Socialisme", "AOKI: World Premiere", "Pacquiao-Cotto 24/7", "Humpday", "Objectified", "Capitalism: A Love Story", "Hanyo", "Sonicsgate", "Photos: Minneapolis" and "TRAILER: Wapakman". The 2010 edition gained 30 pages, mostly the 2008–2010 monthly archives plus the contact page, "What the f___ is RSS?", "The Murder of Fred Hampton Revisited" and "Mga Kababayan (tribute to Francis M)". This retry skipped the edition's other known failures (mostly dead image hosts).
- **LiveJournal: 22 pages and 1 stylesheet**: the profile, friends lists and filtered views, memories, and 15 reply pages from entries 16954 and 17222 (October 2011). Three later captures (2025) are marked `needs_review`.
- **bluescholars.com:** 130 queued page URLs were tried, and one was recovered: a 2023 capture of the "Coffee and Snow 2" video post, marked `needs_review`. Most of the others were malformed URLs with Tumblr markup inside the path, or real post URLs whose only captures are HTTP 404 responses. The exact URL-index query found no other captures. Outcomes are in `wayback-pages-pass.json`.

Wayback refused connections twice more during this pass. The first time came after about 20 requests at a 5-second interval; the second came after about 50 at an 8-second interval. Each time the guarded runner stopped and left the work queued; no false failure records were written.

### Gaps

- The new Sabzi pages link four `site.css?…part=N` stylesheets of Squarespace build `620-05142015`. Neither Common Crawl nor Wayback has those parts; Wayback has only the combined `site.css` of that build (2023). The pages build and pass the check, but they will lack the site styling offline. The existing 2019 pages use builds 621 and 622, which are recovered.
- Mass Line: the two 2007 forum captures excluded by the old filter were not retried in this pass (recovered in the third pass below).
- About 120 real bluescholars.com post and attachment URLs remain queued or failed with no usable capture in Wayback or Common Crawl.

### Verification

All 356 tests pass. The `/bluescholars/` candidate build succeeded with 1,171 recovered pages (1,147 after the first pass). Spot-checked built pages include `/prometheusbrown/2009/blog/2009/11/aoki-world-premiere/`, `/prometheusbrown/2010/blog/contact/` and `/sabzi/2019/blog/seattle-1/`. The candidate check again reported 5,354 errors, all under `206proof/`, for the worktree environment reason given above. No human visual review was done. `visual_fidelity_verified` and `publish_approved` remain false.

## Third pass — November 2, 2026

Wayback, at an 8-second interval, with no connection refusals this time. Outcomes are in `recovery/batches/2026-11-01-commoncrawl-pages/wayback-third-pass.json`.

- **LiveJournal: 3 pages.** These are reply pages from entry 17222 (`replyto=55622`, `56134` and `56902`). Seven other queued URLs failed again, and two stay queued.
- **Mass Line: 2 forum pages.** These are the two 2007 captures the old substring filter rejected because they contain "Socialist". One is the print view of topic 3335, "Counter Intel in the Central District" by JulieC (September 25, 2007). The other is the showPosts page for member GCL1 (`u=77`, October 20, 2007). Both are genuine forum content and now build at `/massline-forums/topic-3335-page-0-e7d9e99332.html` and `/massline-forums/capture-592ca8cb376e.html`.
- The three 2009 `/smf/` captures (`20090407080655`, `20090407081936` and `20090524040017`) still match whole-word spam terms. They remain excluded.

Verification: all 356 tests pass. The candidate build has 1,174 recovered pages. The check again reports 5,354 errors, all under `206proof/`.
