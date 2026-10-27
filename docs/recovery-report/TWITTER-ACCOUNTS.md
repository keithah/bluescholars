# Twitter account recovery

Checked October 27, 2026. The five accounts linked by recovered Blue Scholars pages and feeds are preserved separately: `@BlueScholars`, `@prometheusbrown`, `@sabzi`, `@wongweezy`, and `@canhsolo`. Other accounts mentioned by collaborators or articles were not treated as official Blue Scholars accounts.

## Dated profile pages

Each account inventory uses exact root-page CDX searches for `twitter.com/{handle}`, `mobile.twitter.com/{handle}`, and `x.com/{handle}`. The inventories retain status-200 HTML rows, including alternate original URLs, duplicate timestamps with different digests, and provider-error pages. Raw HTML is marked verified only when its SHA-1 matches its CDX digest. Verified pages are rendered as local dated captures with scripts and remote image fallbacks disabled. Tweet text is indexed with the source capture retained; duplicate posts can appear across snapshots.

| Account | Indexed profile mementos | CDX-verified raw profiles | Capture years | Extracted post entries | Image/style/media references: recovered / unresolved | Unique local payloads |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| Blue Scholars | 38 | 38 | 2009–2026 | 669 | 747 / 91 | 304 |
| Prometheus Brown | 40 | 39 | 2009–2025 | 610 | 704 / 100 | 374 |
| Sabzi | 23 | 23 | 2009–2025 | 255 | 334 / 29 | 186 |
| Wong Weezy | 27 | 26 | 2009–2024 | 341 | 390 / 100 | 271 |
| Canh Solo | 4 | 4 | 2014 | 40 | 36 / 1 | 19 |
| **Total** | **132** | **130** |  | **1,915** | **2,211 / 321** | **1,154** |

The media-reference count is a capture-date/source-URL pair count, not a count of distinct pictures. Across the five inventories there are 2,532 pairs and 1,154 locally saved, content-addressed payloads. The remaining 321 pairs have no validated local payload. Most last returned HTTP 404; some returned empty GIFs or non-image responses. These are exact lookup outcomes, not proof that a file never existed elsewhere.

The linked-reference inventory currently covers image, stylesheet, poster, and audio/video URLs found directly in the captured HTML. It does not recursively CDX-index every `url(...)` dependency inside recovered stylesheets. Unsupported remote CSS dependencies are removed from the offline render, so some archived background images, sprites, and decorative elements may be absent even when the stylesheet itself was recovered.

The 132 profile mementos include one Wong Weezy response whose body does not match the CDX digest and one Prometheus Brown X response that returned no HTML. Wong's mismatched response is retained as unverified bytes. A later Prometheus Brown capture is classified as an account takeover and is not represented as artist-authored material. A current account name or later content does not prove continuity of ownership.

An expanded media pass found a 2015 MP4 linked from two Wong Weezy captures, with a poster in each capture. All four dated media references now resolve to verified local MP4/image payloads and render through a local player. No remote media host is needed for playback. The raw source URLs, CDX evidence, payload SHA-256 values, and capture relationships are in the per-account manifests.

One bounded alternate-date retry recovered one additional Blue Scholars asset from a different exact-URL capture. It checked 75 failed references each for Blue Scholars, Prometheus Brown, and Wong Weezy, and one for Canh Solo. The Blue Scholars batch found one file; the other batches found none. Seventeen Blue Scholars, 25 Prometheus Brown, and 25 Wong Weezy failed references remained untried in those bounded retry batches. Sabzi's 27 newly found page-two references were fetched separately; 24 succeeded and three remain unresolved. Each manifest records its latest attempt count and remaining queue so retries can resume.

## Observed page-two links

The profile HTML contains exact `page=2` links with `max_id` values. The resumable recovery script inventories each full query URL and checks its HTTPS, HTTP, explicit port-80, and mobile-Twitter forms. The refreshed inventory contains five Blue Scholars page-two mementos and four Sabzi mementos; four of the nine responses match their CDX SHA-1. The fifth Sabzi response is preserved as unverified because the body digest differs. The verified Blue Scholars response is a 2020 Twitter error page. Sabzi's 2022 mementos render profile content and do not establish that the old `max_id` was honored. The Prometheus Brown account has four observed targets and no indexed mementos for them. A “more” link without a local response opens the matching capture-filtered local post index and retains the exact Wayback URL as a source lead.

The latest bounded recheck completed without a CDX rate limit. It confirmed four Blue Scholars targets still have no indexed response and all four Prometheus Brown targets remain unindexed. A “not indexed” result is limited to these exact query variants and this check; it is not a global absence claim. Per-target responses and errors are recorded in each account's `pagination-cdx.json` and `manifest.json`.

## Reproduce and resume

Profile inventory and recovery:

```sh
PYTHONPATH=. .venv311/bin/python scripts/recover_twitter_profiles.py --accounts prometheusbrown bluescholars sabzi wongweezy canhsolo --max-files 200
```

Continue newly discovered image, CSS, and media references without rechecking prior failures:

```sh
PYTHONPATH=. .venv311/bin/python scripts/recover_twitter_assets.py --account HANDLE --max-files 1000 --delay 1.5 --timeout 25
```

Retry failed exact references and check for another dated capture after the archive is responsive:

```sh
PYTHONPATH=. .venv311/bin/python scripts/recover_twitter_assets.py --account HANDLE --max-files 1000 --delay 1.5 --timeout 25 --retry-failed
```

Recheck observed page-two URLs:

```sh
PYTHONPATH=. .venv311/bin/python scripts/recover_twitter_pagination.py --max-pages 200 --delay 1.5 --timeout 20
```

The normal static build creates local account indexes, dated captures, tweet search pages, pagination links, and available media players. The site remains an unreviewed recovery preview. This report does not claim complete account ownership history, complete media recovery, human visual review, redistribution clearance for third-party content, or final release approval.
