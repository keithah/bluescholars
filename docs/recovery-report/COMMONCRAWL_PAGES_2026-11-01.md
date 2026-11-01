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
