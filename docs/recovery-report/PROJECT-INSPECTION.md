# Supplied project inspection — October 15, 2026

This is a read-only inspection of `bluescholars-project.zip` supplied in the conversation. It is not a GitHub repository read or proof that a workflow has run.

| File inspected | Observed behavior | Consequence for recovery |
| --- | --- | --- |
| `restore/state.py` | `State.seed()` reads `pages` and `assets` from `recovery/seeds/inventory.json`; it does not consume `video_embeds`. | The expanded compatible seed file adds 56 page/image targets; videos and external posts need separate handling. |
| `restore/urls.py` | `is_site()` accepts apex and www. `in_domain()` includes subdomains. Main-site identity normalization keeps query strings. Unknown external extensions default to image candidates. | Link-following scope is narrower than domain indexing. Extensionless images are not automatically rejected by their suffix. |
| `restore/discover.py` | HTML anchors are added only for `is_site()`. CSS, images, responsive/lazy attributes, some block JSON, and JSON-LD are parsed. | External reblog articles and arbitrary inline configuration are not automatically mirrored. No general archived JSON/RSS collection parser was established. |
| `restore/recover.py` | Supports domain/exact/prefix CDX indexing, resumable cursors, raw acquisition, SHA256, actual capture timestamps. Resources after target become `needs_review`. | Fetching does not establish historical compatibility. The homepage photo is a specific later-than-target review case. |
| `restore/recover.py` / `restore/urls.py` | Fonts, scripts, and unsupported binary classes are excluded. | A known link or metadata ID does not equal a recovered video/audio/font file. |
| `restore/__main__.py` | Provides `seed`, `index`, `recover`, `status`, `build`, `check`, `serve`, `promote`, and `approve`. | Commands in the report reflect the supplied interfaces. Their online success is untested here. |
| `.github/workflows/recover.yml` | Manual recovery, raw/checkpoint artifact upload, candidate build, no Pages publication step. | Acquisition and publication are separate. Artifact upload is intended even after an acquisition failure, subject to workflow execution. |
| `README.md` | Documents script removal, media links, source promotion, review gates, and empty-source limitations. | The package is a toolset, not a completed faithful visual restoration. |

The supplied verification report records 71 passing tests from the earlier implementation session. Tests were not rerun for this research-only report, and that earlier number is not new online or visual verification.

No product code, recovery checkpoint, remote repository, DNS, or deployment was changed. The report's raw-candidate/index URLs are instructions, not saved responses. Keep the full original file inventory and a separate reviewed-source catalog; do not place this report's manifest directly into the project's reviewed catalog.
