# Restoration work log

## 2026-10-15

- Extracted the complete handoff into the empty workspace and checked that it contained no `.git` directory or recovered site files.
- Confirmed GitHub CLI is authenticated as `keithah`; `GET /repos/keithah/bluescholars` returns 404, so the target repository is absent or inaccessible to this account. No repository existed locally before extraction.
- Installed the supplied development dependencies in `.venv311` using Python 3.11. The system Python 3.9/pip environment could not resolve the pinned package; Python 3.11 resolved it without changing dependency declarations.
- Baseline: `.venv311/bin/python -m pytest -q` — 71 passed.
- Merged the expanded report inventory into `recovery/seeds/inventory.json`, preserving existing metadata and deduplicating page and image entries by full original URL. Result: 14 page/query targets, 42 image targets, and 11 ordered video references. Loaded these with `python -m restore seed`: 56 queued page/image URLs.
- Began a bounded, resumable domain CDX query with `python -m restore index --max-pages 20 --delay 1.2`. A direct raw replay of the selected May 29, 2021 homepage returned HTTP 200, 35,243 bytes, HTML, SHA-256 `18c5bcc0e9866c3129854f786782ba95b58e9747a4a672626ffccb34ce3bc75b`. This probe was outside the recovery tool and is not yet included as an acquired/provenance record.

## Decisions and next steps

- Continue with the existing resumable recovery tooling; preserve every source URL, resolved capture, and hash.
- Create/push to the authorized public `keithah/bluescholars` repository only after committing the project baseline. Do not enable Pages until actual source recovery and review gates pass.
- Acquire the domain index and seeded sources in paced batches. Fix recovery/parser/build issues exposed by actual archived input, with regression coverage.
- Keep Pages disabled unless original homepage markup, local original CSS and principal imagery, root/subpath checks, browser comparisons, compatibility decisions, and accurate provenance reports all pass.
