# Portable Blue Scholars restoration package

The companion ZIP contains the reviewed source catalog and content-addressed payloads, the resumable acquisition state and raw recovery payloads, the generated `/bluescholars/` static site, restoration tools, tests, and recovery reports. It excludes Git history, virtual environments, generated backup trees, Python/test caches, credentials, and font binaries.

To rebuild from this folder with Python 3.11 or newer, install `requirements-dev.txt`, then run:

```bash
python -m restore build --base-path /bluescholars
python -m restore check --base-path /bluescholars
```

The included `/bluescholars/` candidate reflects the 2026-10-20 recovery checkpoint: 1,065 recovered pages (including 12 feeds), 2,170 explicit placeholders, one derived page, and 1,584 local main-site source assets. It also includes the separate Prometheus Brown Twitter archive: 34 captured profile responses rendered as local dated pages, 675 of 774 linked asset/capture pairs recovered (357 unique payloads), three provider-error captures, and one later account-takeover capture kept distinct from artist-authored content. The remaining 99 linked Twitter assets returned 404 for the captured URL; alternate snapshots have not been exhausted.

The main recovery index is complete for its recorded query set, not for all historical URLs. It currently records 12,822 resource URLs, 165,338 capture rows, 4,981 recovered records (2,741 unique payloads), 283 later resources held for review, 4,898 queued resources, and 2,656 failed resources. The candidate records thousands of source gaps and has not passed release review. Fresh root-mounted and `/bluescholars/` candidate checks passed with zero errors for this checkpoint. The full suite passes 264 tests. See `GAP_REPORT.json`, `current-checkpoint.json`, and `VISUAL_REVIEW.md` for coverage and limitations.

The owner confirmed permission to publicly redistribute the archived material; this attestation is recorded separately from publication approval. Credential-shaped API values in 692 unique payloads / 1,139 source references are omitted from public source copies, with exact originals retained only in the ignored local recovery cache and excluded from this package. This remains an incomplete preview, not a reviewed final release. A package checksum is supplied alongside the ZIP.
