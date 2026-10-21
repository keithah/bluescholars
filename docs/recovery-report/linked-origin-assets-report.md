# Linked-origin image recovery — October 20, 2026

The bounded recovery workflow requested exact image URLs observed in preserved Blue Scholars source material from four Squarespace CDN hosts. Redirects stayed within that allowlist; observed HTTP URLs used HTTPS transport. The response bytes are hash-addressed and retained locally.

It acquired **416 linked-origin responses (7,092,026 bytes)**, of which **412 are renderable images (6,915,638 bytes)**. Four SVG icon-font URLs were retained as evidence but excluded from image rendering because they are fonts, not photos or page illustrations. The exact source URLs, final URLs, referrers, source-capture hints, response types, hashes, and failures are itemized in [linked-origin-assets-report.json](linked-origin-assets-report.json).

These are direct CDN responses, **not Wayback captures**. The CDN response cannot prove when it was historically served. Its exact upload URL and its appearance in archived source pages provide the provenance. 404 and non-image replies remain gaps; no replacements were invented. This preservation evidence does not establish redistribution rights.

Resume bounded discovery with `python -m restore recover-origin-images --max-files 100 --delay 0.5`. The workflow only accepts linked Squarespace CDN image URLs and does not crawl arbitrary hosts.
