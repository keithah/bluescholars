# Mass Line Media archive recovery

This is a separate historical source collection for `masslinemedia.com`; its forum is preserved as its own browsable area. Captured pages retain source URLs, exact Wayback timestamps, byte counts, and SHA-256 hashes. Recovered raw bytes are kept under `recovery/massline/raw/`.

## Archive evidence

- The collapsed CDX index has **5,356 URL records**; the separate uncollapsed query has **7,121 capture events**. Of the URL records, **4,645** are HTML under `/smf/`, **4,014** have a topic query, **672** topic IDs appear, and **9** board IDs appear.
- The root-history queries yielded **213** distinct homepage capture records. Representative root captures were inspected individually across 2006–2026.
- The latest substantial authentic Mass Line homepage inspected is the 2009 capture below. The later root captures inspected are parked, unrelated replacement, domain-sale, or JavaScript/challenge pages, so they are retained as index evidence and excluded from the restoration.

## Homepage captures selected

- **2006** — `20061231081225`; 22,489 bytes; [captured source](https://web.archive.org/web/20061231081225id_/http://masslinemedia.com:80/)
- **2007** — `20071231082843`; 18,438 bytes; [captured source](https://web.archive.org/web/20071231082843id_/http://masslinemedia.com:80/)
- **2008** — `20081026114152`; 24,728 bytes; [captured source](https://web.archive.org/web/20081026114152id_/http://www.masslinemedia.com:80/)
- **2009** — `20090813183844`; 19,805 bytes; [captured source](https://web.archive.org/web/20090813183844id_/http://www.masslinemedia.com:80/)

## Recovery status

- Saved: **1,144** indexed resources plus **4** homepage versions (1124 HTML pages, 14 images, 6 stylesheets, 0 media files; 43,460,325 bytes).
- Unavailable or invalid responses: **0**; pending indexed resources: **4,088**. Current crawl complete: **false**.
- Captured images and styles are mapped locally. Scripts are never run; forms and embedded players are disabled in the static copy. Explicit source links may open the Wayback replay when a page or asset is not stored locally.
- The candidate is not promoted into the reviewed source catalog and is not a release or human review. No Pages deployment was made as part of this recovery step.

## Resume

```bash
python -m restore massline-index
python -m restore massline-history --max-pages 1
python -m restore massline-recover --max-files 250 --delay 0.4
python -m restore build --candidate --base-path /bluescholars
python -m restore check --candidate --base-path /bluescholars
```

The uncollapsed event inventory is saved in `recovery/massline/all-captures.json`; do not describe the collapsed URL count as every capture event. The current page builder chooses the latest captured URL response on or before August 31, 2009 and stores superseded downloaded versions separately.
