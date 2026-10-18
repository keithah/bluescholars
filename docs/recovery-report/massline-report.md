# Mass Line Media archive recovery

This is a separate historical source collection for `masslinemedia.com`; its forum is preserved as its own browsable area. Captured pages retain source URLs, exact archive timestamps, byte counts, and SHA-256 hashes. Wayback raw bytes are under `recovery/massline/raw/`; linked offsite assets are under `recovery/massline/external/raw/`.

## Archive evidence

- The collapsed CDX index has **5,356 URL records**; the separate uncollapsed query has **7,121 capture events**. Of the URL records, **4,645** are HTML under `/smf/`, **4,014** have a topic query, **672** topic IDs appear, and **9** board IDs appear.
- The root-history queries yielded **213** distinct homepage capture records. Representative root captures were inspected individually across 2006–2026.
- The latest substantial authentic Mass Line homepage inspected is the 2009 capture below. The later root captures inspected are parked, unrelated replacement, domain-sale, or JavaScript/challenge pages, so they are retained as index evidence and excluded from the restoration.

## Homepage captures selected

- **2006** — `20061231081225`; 22,489 bytes; [captured source](https://web.archive.org/web/20061231081225id_/http://masslinemedia.com:80/)
- **2007** — `20071231082843`; 18,438 bytes; [captured source](https://web.archive.org/web/20071231082843id_/http://masslinemedia.com:80/)
- **2008** — `20081026114152`; 24,728 bytes; [captured source](https://web.archive.org/web/20081026114152id_/http://www.masslinemedia.com:80/)
- **2009** — `20090813183844`; 19,805 bytes; [captured source](https://web.archive.org/web/20090813183844id_/http://www.masslinemedia.com:80/)
- **2009-07** — `20090704090847`; 18,981 bytes; [captured source](https://index.commoncrawl.org/CC-MAIN-2009-2010-index?url=http%3A%2F%2Fwww.masslinemedia.com%2F&output=json)

## Recovery status

- Saved: **1,744** indexed resources plus **5** homepage versions (1421 HTML pages, 313 images, 6 stylesheets, 4 media files; 90,846,223 bytes).
- Unavailable or invalid responses: **0**; pending indexed resources: **3,488**. Current crawl complete: **false**.
- Captured images and styles are mapped locally. Scripts are never run; forms and embedded players are disabled in the static copy. Explicit source links may open the source archive when an item is not stored locally.
- External assets referenced by recovered pages: **602** exact URLs discovered; **170** have Wayback capture records (0 indexed and awaiting download, 156 recovered); **431** returned no capture, **14** had only non-image/error payloads, **1** index queries and **0** payloads are retryable failures, and **0** remain queued. Locally captured: **156** (156 images, 0 media files; 9,246,018 bytes).
- Forum browsing: nine captured boards are grouped by their source titles. Each of the 239 locally captured topic IDs has a landing page listing its saved page-offset and individual-message snapshots by exact Wayback timestamp; each entry opens the preserved SMF capture. This is a navigation aid over the recovered source pages, not a reconstruction of uncaptured posts.
- Independent archives: Common Crawl `CC-MAIN-2009-2010` supplied a separately preserved July 4, 2009 homepage; Arquivo.pt returned no forum captures and its two site records replay as HTML fallback pages. Detailed queries and raw observations are under `recovery/massline/external/`.
- The raw media files are archival source material; archive availability is not a redistribution license. The candidate is not promoted into the reviewed source catalog and is not a release or human review. No Pages deployment was made as part of this recovery step.

## Resume

```bash
python -m restore massline-index
python -m restore massline-history --max-pages 1
python -m restore massline-recover --max-files 250 --delay 0.4
python -m restore massline-external-index --max-assets 50 --delay 2.0
python -m restore massline-external-recover --max-files 40 --delay 0.6
python -m restore build --candidate --base-path /bluescholars
python -m restore check --candidate --base-path /bluescholars
```

The uncollapsed event inventory is saved in `recovery/massline/all-captures.json`; do not describe the collapsed URL count as every capture event. The current page builder chooses the latest captured URL response on or before August 31, 2009 and stores superseded downloaded versions separately.
