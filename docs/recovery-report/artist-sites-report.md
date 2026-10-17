# Prometheus Brown and Sabzi archive recovery

Source pages remain separated by host and dated edition. The machine-readable report lists every recovered capture and known failed or unavailable linked resource.

## Internet Archive index coverage

- `prometheusbrown.com`: 1580 successful CDX rows across 676 normalized URLs; available timestamp years: 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026.
- `sabzi.co`: 322 successful CDX rows across 119 normalized URLs; available timestamp years: 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022.

## Recovered editions

- `prometheusbrown.com/2008`: 29 locally saved responses; 97 unresolved or excluded linked resources; crawl queue drained.
- `prometheusbrown.com/2009`: 278 locally saved responses; 659 unresolved or excluded linked resources; crawl queue drained.
- `prometheusbrown.com/2010`: 456 locally saved responses; 1420 unresolved or excluded linked resources; crawl queue drained.
- `prometheusbrown.com/2013`: 1 locally saved responses; 6 unresolved or excluded linked resources; crawl queue drained.
- `prometheusbrown.com/2016`: 11 locally saved responses; 2 unresolved or excluded linked resources; crawl queue drained.
- `prometheusbrown.com/2019`: 8 locally saved responses; 4 unresolved or excluded linked resources; crawl queue drained.
- `prometheusbrown.com/2022`: 41 locally saved responses; 3 unresolved or excluded linked resources; crawl queue drained.
- `sabzi.co/2013`: 47 locally saved responses; 104 unresolved or excluded linked resources; crawl queue drained.
- `sabzi.co/2016`: 69 locally saved responses; 5 unresolved or excluded linked resources; crawl queue drained.
- `sabzi.co/2019`: 61 locally saved responses; 6 unresolved or excluded linked resources; crawl queue drained.
- `sabzi.co/2022`: 3 locally saved responses; 4 unresolved or excluded linked resources; crawl queue drained.

## Source-integrity notes

The acquisition contains 674 unique SHA-256 payloads. Each recovered record retains the original URL, capture timestamp, Wayback source, and CDX digest when available.
A sampled Prometheus Brown `/0.html` capture from 2009-09-01 is spam-injected (its page title is ‘Cialis Get Viagra’), while the `/blog/` capture from 2009-12-28 is a genuine Prometheus Brown WordPress blog. Those are kept distinct. Eight unique 2024 root digests (15 index rows) were inspected individually; all are spam-injected JAYA77 casino pages. They are not treated as artist-site editions. 2024–2026 rows remain in the source index for continued review, and the latest selected artist homepage remains 2022.
Missing linked resources are listed in `artist-sites-report.json`; a failed dependency is not silently replaced with a live asset. Dynamic Gravatar profile-image URLs are listed as excluded gaps. Site pages have scripts, embedded remote frames and forms removed; CSS/image rendering dependencies are local-only in generated output.
