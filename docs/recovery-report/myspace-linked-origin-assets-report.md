# MySpace linked-origin image recovery — 2026-10-20

The archived profile HTML contains exact image URLs on the original MySpace CDN. A bounded, resumable pass attempted **109** URLs: **1** yielded one distinct image suitable for local rendering, **18** returned MySpace’s generic camera placeholder, and **90** failed (including CDN HTTP 429, unavailable legacy DNS, and TLS handshake errors). The camera placeholders and failed responses are preserved in the itemized inventory but are not substituted into the profile. A single source URL yielded a distinct small profile image; it is mapped locally. The CDN sent identical placeholder bytes for many unrelated image keys, which is why a successful HTTP status alone was not treated as successful visual recovery.

These are direct origin responses, not dated Wayback captures. Archived source capture dates are retained only as evidence that each exact URL was linked from the profile. No capture timestamp is assigned to CDN responses. The workflow is restricted to observed raster image URLs on `*.myspacecdn.com`, follows redirects only within that family, and disables automatic fallback to other hosts. The complete URL-level outcomes and provenance are in [myspace-linked-origin-assets-report.json](myspace-linked-origin-assets-report.json).

The inventory contains 1,384 eligible exact raster URLs on the MySpace CDN; 1,278 have not been attempted. Resume with a paced batch (respecting the CDN cooldown):

```bash
.venv311/bin/python -m restore myspace-origin-recover --max-files 100 --delay 1.2
```

Retry previously failed URLs only when useful; already recovered files and identified generic placeholders are skipped:

```bash
.venv311/bin/python -m restore myspace-origin-recover --max-files 100 --delay 1.2 --retry-failed
```
