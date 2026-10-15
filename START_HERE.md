# Blue Scholars — complete Codex handoff

This folder combines **all four earlier deliverables**: the full recovery/static-site project, the expanded recovery report and inventories, the earlier reconnaissance handoff, and the original restoration design. The earlier files are preserved byte-for-byte and arranged together; nested duplicate ZIPs are not necessary.

**What is not here:** recovered original website HTML/CSS/photos/media, a created remote repository, or a deployed site. The starter project is working recovery/build tooling with an empty reviewed-source catalog. The research report locates sources; it is not a downloaded mirror.

## Use it in Codex

Extract the ZIP and open **this `bluescholars` folder** as the Codex project/workspace. Make the folder available in the execution environment; attaching only a ZIP without opening/extracting it may not give the agent a usable project. Paste:

```text
Read CODEX_PROMPT.md in this workspace and execute the full task end to end.

Use the existing code, the expanded recovery report and all inventories in this folder. Restore bluescholars.com faithfully from the May 29, 2021 homepage reference, searching other archive dates and linked assets to recover as much as possible. Do not stop at planning, a scaffold, or placeholder pages.

I authorize creating the public keithah/bluescholars repository if absent, implementing and testing the restoration, committing and pushing the work, running recovery workflows, and enabling/deploying GitHub Pages after the documented recovery, visual-review, and release gates genuinely pass. Preserve existing work. Do not change DNS, add a custom domain, force-push, delete history, spend money, or expose credentials.

Proceed autonomously through ordinary decisions. Check current GitHub authentication and repository state rather than assuming the earlier reports describe them now. Ask only for a genuine permissions/authentication blocker or a destructive conflict. Never claim that downloaded content, human review, tests, or deployment occurred without evidence.

Start by inspecting the project and running its existing tests, then merge the expanded seeds and recover actual source files. Finish with the real repository/commit, verified deployment URL if released, source and gap reports, screenshots when available, and exact remaining blockers/resume instructions.
```

The full `CODEX_PROMPT.md` is the task specification. It includes capture priorities, known pitfalls, the current CLI, safe recovery/resume handling, visual checks, and conditional publication authorization.

Authentication, available network access, and the agent's ability to run commands are still required. There are no credentials in this handoff. Use the normal authenticated GitHub tooling; do not paste a token into the prompt. Leave source/publication approval false until the documented conditions have actually been met.

## Folder map

| Location | Contents |
| --- | --- |
| `CODEX_PROMPT.md` | Complete execution prompt |
| `restore/`, `tests/`, `scripts/`, `.github/workflows/` | Original working recovery/build project |
| `README.md` | Original setup, acquisition, promotion, and Pages instructions |
| `docs/recovery-report/REPORT.md` / `REPORT.html` | Full expanded source-location report |
| `docs/recovery-report/recovery-manifest.csv` / `.json` | 97 researched URL records, not 97 recovered files |
| `docs/recovery-report/recovery-seeds-expanded.json` | 14 page/query targets, 42 images, 11 video references |
| `docs/recovery-report/capture-search-queries.csv` | 31 targeted archive queries |
| `docs/recovery-report/blog-entry-checklist.csv` | 40 observed blog-entry finding aids |
| `docs/recovery-report/REQUEST-OBSERVATIONS.md` | Recorded request outcomes and limitations |
| `docs/recovery-report/PROJECT-INSPECTION.md` | Existing code's behavior and acquisition limitations |
| `docs/recovery-report/observed-archive-urls.txt` | Previously observed archive URLs |
| `docs/recovery-handoff/` | Earlier reconnaissance, seed inventory, queue, and design |
| `docs/reference/` | Original separately delivered restoration design |
| `docs/handoff/PACKAGE_VERIFICATION.md` | Fresh local packaging/baseline checks |
| `HANDOFF_CONTENTS.json` | Original-to-bundled file mapping and hashes |
| `HANDOFF_CHECKSUMS.sha256` | SHA-256 inventory of packaged files other than itself |

The current active seed inventory remains unchanged for reproducibility: **9 pages and 5 images**. Codex is explicitly instructed to merge the expanded seed file before acquisition. No original source bytes were added during packaging. The earlier verification reports remain historical; see the new packaging verification for the fresh test run.

## Optional integrity check

From this directory:

```bash
# macOS
shasum -a 256 -c HANDOFF_CHECKSUMS.sha256

# Linux (alternative)
sha256sum -c HANDOFF_CHECKSUMS.sha256
```

The checksums describe the handoff as delivered. They are not expected to match files after Codex edits the project.
