# Mass Line Media: other archive and linked-asset search

This report covers independent sources and off-domain files linked by the recovered Mass Line pages. It is a bounded search log, not a claim that every archive or capture service has been exhausted. The full responses and per-URL checkpoints are in [`recovery/massline/external/`](../../recovery/massline/external/).

## Internet Archive Wayback

The full `masslinemedia.com/*` CDX inventory contains 7,121 capture events across 5,356 URL keys. The asset-first recovery pass raised the local domain cache to 1,544 resources: 1,221 HTML pages, 313 images, 6 stylesheets and 4 media files, plus five homepage captures. The four audio files are ID3/MP3 streams; `ffprobe` identified durations of 190.69, 219.43, 256.06 and 230.77 seconds. Their raw bytes and source capture timestamps are in `recovery/massline/raw/`.

Parsing recovered pages found 601 unique external image/media URLs across off-domain hosts. Paced exact-URL Wayback queries returned capture records for 57 of those URLs; 55 image files passed signature validation. A separately discovered YouTube thumbnail adds one more capture, bringing the locally preserved external images to 56 (3,532,768 bytes) and the current external inventory to 602 URLs. The index now has 56 recovered, 63 no-capture, 2 HTML/error-only, and 481 queued records. Ten newly recovered images came from the latest batch. Sixteen requests initially hit rate limits; the checkpointed queue resumed at a two-second delay and those index errors cleared. The indexer honors `Retry-After` and records cooldowns.

The domain index includes ten MP3-looking URL records. Four contain actual ID3 audio streams, with durations of 190.69, 219.43, 256.06 and 230.77 seconds. The other six replay as HTML, redirects or 404 pages, not audio. Exact record metadata is saved in `recovery/massline/external/media-search.json`.

Recovered 2006 pages include four distinct YouTube video IDs. Wayback has a 2017, 2022 and 2024 capture of one thumbnail (same image digest); the 2017 JPEG is locally stored and linked to the 2006 source pages. The other three thumbnail URLs have no Wayback captures. Exact quoted Internet Archive item searches for all four IDs found no items. No actual video file was recovered; IDs, source-page timestamps, thumbnail capture rows and search results are recorded in `recovery/massline/external/video-embeds.json` and `youtube-thumbnail-index.json`.

One especially useful linked image was hosted on MySpace’s old image CDN. The 2011 JPEG is a real 400×1025 Gabriel Teodros show flyer and is now mapped locally on the separately preserved July 2009 homepage. The 2012 and 2016 captures of the same URL are only 90×90 gray placeholders; their CDX entries and individual assessments are preserved in `recovery/massline/external/myspace-cdn-image.json`, and the placeholders are not displayed.

## Common Crawl

A query of `CC-MAIN-2009-2010` returned 41 status-200 records, including 21 dated in 2009. Its July 4, 2009 homepage WARC record was recovered and checked as genuine “MASS LINE MEDIA” HTML (18,981 response bytes). It is preserved as a distinct homepage variant beside the later August 2009 Wayback page, with WARC file, compressed offset/range, source-index link and SHA-256 recorded in the manifest. A separate exact-URL search checked six missing MP3 URLs in 12 selected Common Crawl indexes. It found no media rows; 61 of 72 requests timed out or were refused, five returned HTTP 404 and six returned HTTP 504, so this result is incomplete rather than proof of absence. Full per-index outcomes are checkpointed in `recovery/massline/external/media-commoncrawl.json`.

A 2012 root WARC record was also retrieved and inspected individually. It is a German jewelry site (“Dokumente für Sie moderiert”), so it is excluded as an unrelated use of the domain. The other saved 2012 index rows point to that same jewelry site’s routes. Selected probes of 13 Common Crawl indexes were not exhaustive: most returned 503, timeout or connection-refused responses. An initial 2014 index request briefly returned a few rows, but the full response was not checkpointed and later retries were refused; it is not used as recovered source material. Per-index results and errors are saved in `recovery/massline/external/commoncrawl-selected.json`.

## Arquivo.pt and other services

Apex and `www` Arquivo.pt CDX searches returned the same two site records: `news/newspics/101.jpg` and `robots.txt`. Their replay URLs each returned a 3,032-byte HTML fallback page, not image or robots bytes. Exact `/smf/*` queries for both host spellings returned no forum rows. Raw query responses and replay observations are in `recovery/massline/external/arquivo-pt.json`.

The Memento Time Travel endpoint could not be resolved from this environment. No forum or media file recovery was obtained from Arquivo.pt or Memento in this pass.

## Resume

The external URL inventory is checkpointed, so continue without rescanning the 1,200+ local HTML pages:

```bash
.venv311/bin/python -m restore massline-external-index --max-assets 50 --delay 2.0
.venv311/bin/python -m restore massline-external-recover --max-files 40 --delay 0.8
```

After new page captures are added, refresh the external URL discovery once:

```bash
.venv311/bin/python -m restore massline-external-index --max-assets 50 --delay 2.0 --refresh-discovery
```

The current candidate is still unreviewed and not deployed. Archive availability does not establish a redistribution license for the audio, photos, forum posts or other original material.
