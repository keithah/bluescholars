# Blue Scholars MySpace profile recovery

The separate profile archive is [myspace.com/bluescholars](https://myspace.com/bluescholars). Exact Wayback CDX queries covered the apex and `www` on HTTP and HTTPS. They returned 91 unique successful HTML capture rows spanning 2007–2025. Each date was individually replayed and the payload checked: 89 valid HTML responses (12,872,299 bytes) are saved as hashed source files, while two July 2008 responses still fail gzip decoding. The valid rows resolve to 88 distinct capture timestamps; requested and resolved dates remain separate in the index. The gallery generates a local page for every validated response, but the snapshots have not each been visually reviewed by a person.

The page captures expose 1,561 unique image/media and stylesheet URLs: 1,428 images/media URLs and 133 CSS URLs. Exact CDX lookups were completed for all 1,561. Seven bounded retries have checked 280 previously rate-limited URLs and found 60 additional capture-bearing URLs: Wayback now has rows for 213 image/media URLs and all 133 stylesheets (346 URLs total). The recovery pipeline has downloaded and validated 210 image/media resources and 133 stylesheets (343 source URLs), totaling 18,162,800 bytes across 314 unique files. This includes seven inline MySpace default-cover images and a profile icon that the initial asset scan missed. The latest retry added a 2007 profile image captured at `20070616041026` (2,563 bytes; SHA-256 `a5a5585b7c11c45adb6f92f0f91e325acf9dc26c4e3c1c426cd1779ac6ed88ab`). Three payloads were rejected because they were HTML or unknown content instead of valid image bytes: two legacy Flash players and `www.masslinemedia.com/images/myspacebg.gif`. Captured CSS is stored locally; active imports and automatic external URL references are stripped from the rendered archive so page loading does not contact the original hosts.

Of the remaining image/media lookups, 1,131 are still rate-limited by Wayback (HTTP 429), and 84 indexed URLs have no capture row. The seven retries were deliberately bounded; recent batches yielded one capture in the latest 30-URL pass, so the remaining index is resumable rather than being hammered. Those states are not treated as proof the original media never existed. The indexes preserve each URL, referrer capture, query result, selected capture, source URL, content type, and SHA-256 where bytes were recovered. A future retry can target only rate-limited rows:

A separate five-URL probe of Internet Archive’s Wayback Availability API returned no parseable JSON; a diagnostic repeat returned HTTP 429. It yielded no captures and does not show that those images are absent. Exact probe URLs, dates and outcomes are preserved in [`availability-probe.json`](../../recovery/myspace-blue-scholars/index/availability-probe.json).

```bash
.venv311/bin/python -m restore myspace-assets-index --max-urls 100 --delay 2.0 --retry-errors
.venv311/bin/python -m restore myspace-assets-recover --max-files 100 --delay 1.0
.venv311/bin/python -m restore build --candidate --base-path /bluescholars
.venv311/bin/python -m restore check --candidate --base-path /bluescholars
```

The 89 local snapshots preserve captured profile text, comments, inline styles and dated appearance, while scripts, forms and interactive players are disabled. The MySpace page gallery has not received human visual review; the broader restoration remains an unreviewed candidate and the Pages release gate remains closed.
