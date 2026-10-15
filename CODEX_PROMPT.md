# Codex task: complete the Blue Scholars website restoration

## Objective and authority

Work in this project and carry the restoration through discovery, source acquisition, static reconstruction, testing, repository setup, and verified GitHub Pages deployment. Deliver working code and recovered content—not another plan, a generic redesign, or an empty scaffold.

Recreate historical **bluescholars.com** as faithfully and completely as recoverable evidence allows. Use this homepage as the visual reference:

https://web.archive.org/web/20210529010817/http://bluescholars.com/

Search other Internet Archive dates, linked pages, and source-linked image hosts to fill gaps. Preserve additional historical content without silently mixing incompatible site designs. The target repository is **`keithah/bluescholars`**, intended to be public. The expected project-site path is **`/bluescholars/`**. Report the actual URL returned by a successful Pages deployment rather than assuming it is live.

I authorize creating that repository if absent, making project changes, committing and pushing the restoration, running its recovery workflows, and enabling/deploying GitHub Pages **after the evidence and release checks below pass**. Preserve unrelated work and existing repository history. Do not change DNS, add a custom domain/CNAME, rename other repositories, enable paid services, purchase anything, delete history, or force-push. If the repository already contains unrelated or conflicting work, keep your changes isolated rather than replacing it.

Proceed autonomously through ordinary, reversible decisions. Do not stop after outlining a plan or repeatedly ask whether to continue. Maintain a short progress ledger and work through the task. Ask only for genuinely missing authentication/permissions, an unresolved destructive conflict, or another decision you cannot safely make. Never request that I paste a token into chat or commit credentials. Earlier documents' planning-stage check-ins are historical; this prompt supplies the execution and conditional publication authorization. Their technical safeguards and truthful reporting requirements still apply.

## Read the existing work before changing it

Start in the folder containing this file. Inspect `pwd`, Git status/remotes if any, and the existing code. Read:

1. `START_HERE.md`, `README.md`, `RIGHTS.md`, and `docs/handoff/PACKAGE_VERIFICATION.md`.
2. `docs/recovery-report/REPORT.md` for the detailed acquisition report. Use `REPORT.html` only as another view of the same report.
3. `docs/recovery-report/recovery-manifest.csv` or its JSON equivalent; `capture-search-queries.csv`; `blog-entry-checklist.csv`; `REQUEST-OBSERVATIONS.md`; and `PROJECT-INSPECTION.md`.
4. `docs/recovery-report/recovery-seeds-expanded.json` and the current `recovery/seeds/inventory.json`.
5. `docs/superpowers/specs/2026-10-15-restoration.md`, `docs/superpowers/plans/2026-10-15-restoration.md`, `docs/IMPLEMENTATION_STATUS.md`, and `docs/VERIFICATION.md`.
6. The `restore/` modules, existing tests, scripts, and `.github/workflows/`.

`docs/recovery-handoff/` and `docs/reference/` preserve the earlier notes/design. Prefer the expanded report for acquisition coverage and actual code for implemented interfaces. The reports contain historical observations, not fresh proof that a URL works today. A report's finding-aid label is not necessarily an original article title.

**Important initial state:** this handoff contains a recovery toolset, not recovered original website files. Its reviewed source catalog is empty and publication approval is false. At packaging, the existing automated suite passed 71 tests. That does not prove online acquisition, visual fidelity, current repository existence, or deployment. The original active inventory contains 9 page targets and 5 images. The expanded inventory contains **14 page/query targets, 42 image URLs, and 11 video references**; the full manifest has **97 records**, including **30 external leads**. The blog checklist contains **40 observed listing entries**, and there are **31 targeted index queries**. These are starting counts, not full archive coverage or numbers of recovered files.

## Workstream 1: establish a runnable project and correct seed inventory

Create a local virtual environment without committing it. Use the supplied dependencies and Python 3.11 or newer; Node is needed for an existing JavaScript regression test. Verify rather than assume that Git, `gh`, and any browser tooling are installed. Prefer this existing Python/static-HTML implementation; do not introduce a framework or package manager just for styling.

Run the current tests before changes. A baseline setup is:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m restore --help
```

Merge `docs/recovery-report/recovery-seeds-expanded.json` into the active `recovery/seeds/inventory.json`, preserving useful prior metadata and deduplicating by the full normalized original URL. It uses the supplied seed schema. Preserve query strings, original paths, capture hints, and referrers. Then load it with `python -m restore seed` and inspect the resulting queue. Do not write the research manifest directly into `source/catalog.json`; researched, queued, downloaded, compatible, and approved are different states.

The current seed loader consumes pages and assets, not video references or external articles. Explicitly plan and implement the handling needed for those other records rather than assuming the expanded JSON makes the entire 97-record manifest crawl automatically.

Reuse and improve existing modules. Add focused regression tests for changed behavior, run the complete suite after meaningful changes, and keep a durable ledger in `docs/WORK_LOG.md` with completed work, decisions, exact blockers, and next commands. Do not redo completed acquisition just because a session restarts.

## Workstream 2: inventory and acquire original sources

### Core starting captures

The detailed report/manifest holds the exact URLs and alternate queries. Start from these known observations and verify the actual resolved response:

| Original path | Starting capture | Observation, not a guarantee of current availability |
| --- | --- | --- |
| `/` | `20210529010817` | Selected homepage/layout reference |
| `/blog/` | `20201109000819` | Readable first listing |
| `/blog?offset=1362122742000` | `20200220154840` | Readable second listing |
| `/blog/2013/9/9/eugene-oregon-august-2013` | `20200220154703` | Individual article and four gallery images |
| `/shows` | `20200703230849` | Page structure; poster still needs recovery |
| `/video` | `20200802161924` | Eleven video embed references |
| `/holler` | `20200703230805` | Historical contact/team content |
| `/shop` | `20200718164929` | Provider error: find a different capture |
| `/blog?offset=1358016466000` | `20190719224039` | Provider error; an earlier June 11, 2016 capture is a lead |

The June 11, 2016 lead does **not** have a verified full timestamp or recovered body in this package. Resolve it with the exact-URL index before claiming recovery. Do not assume the initial 2019 blog capture is usable simply because Wayback archived it.

### Index broadly, download deliberately

Use the Wayback CDX index with pagination/resume keys. Inventory the main domain, apex/`www`, observed protocol variants, relevant subdomains, historical routes, query-based listing pages, tags, author pages, and article permalinks. Retain alternate timestamps and capture digests; do not collapse the only master index to the newest capture or a single digest. Record which query partitions completed, which reached a configured limit, and which failed. Exhausting the seeded queue does not establish archive-wide completeness.

Use `docs/recovery-report/capture-search-queries.csv` as a work queue. Its requests are prepared research queries, not completed query results. Separate observed URLs from speculative endpoints. Inspect raw source for feeds, sitemaps, collection/JSON endpoints, image blocks, inline configuration and redirects; only promote those additional paths to evidence-backed leads when supported. Do not spend unbounded requests guessing URLs.

Existing commands, to be checked against the current CLI:

```bash
python -m restore seed
python -m restore index --max-pages 20
python -m restore recover --max-files 150
python -m restore status
python -m restore index --max-pages 50
python -m restore recover --max-files 500 --retry-failed
```

Use `index --url ACTUAL_OBSERVED_URL --match exact` or `--match prefix` for targeted searches. Repeat bounded batches when state shows unfinished work and requests are succeeding. Do not treat these initial numeric limits as the recovery goal.

Use raw-original replay requests where appropriate and retain untouched responses separately from transformed output. Parse Wayback-wrapped links back to their source identities, but retain the observed wrapper and redirect chain for provenance. Save source URL, request timestamp, actual resolved capture timestamp, referrer, MIME/content validation, byte count, SHA-256, local file path, attempt history, and compatibility/review status. Keep distinct source records even when bytes deduplicate.

Prefer the selected capture and compatible earlier snapshots, not blindly the oldest/newest. Explicitly detect captured provider errors, parked/replaced sites, HTML error bodies returned for image/CSS URLs, and challenge pages—even when HTTP is 200. A cache miss, access denial, or network failure does not prove an asset is missing from the archive.

### Recover dependencies from all observed hosts

The report identifies the following families; use its full URLs, not truncated examples:

- `images.squarespace-cdn.com/content/v1/51b8c20be4b0f1f8c9dcdf4c/…`: 18 observed images.
- `static1.squarespace.com/static/51b8c20be4b0f1f8c9dcdf4c/…`: 15 observed extensionless image URLs.
- `media.tumblr.com/…`: 9 observed inline images.

Prioritize original CSS, header/logo assets, the homepage photograph, navigation, and the core-section images before a large blog backlog. Extract dependencies from HTML, stylesheets and imports, CSS `url(...)`, `src`, `srcset`, lazy-load attributes, block data, background images, and source-linked configuration. Preserve image dimensions, variants, crop information, credits and display order.

Do not restrict image discovery to `.jpg` and `.png`: the older Squarespace URLs end with a timestamp-like segment and slash. Validate bytes and assign a safe local extension. Multiple distinct images are named `image-asset.jpeg`; deduplicate by full source identity/content hash, not basename. Never invent a numbered gallery member: the Eugene gallery references image numbers 1, 2, 4 and 5, not an observed image 3.

Top missing named-image investigations are `EUGENE.jpg`, `scholars.jpg`, and `sisters2.jpg`. For each, search the exact URL across dates, indexed variants within its own asset prefix, compatible older parent HTML, and the specific credited/reblogged source. Do not conclude that every capture is missing after one failed replay.

**Timestamp edge case:** the reference homepage is `20210529010817`; its observed photograph capture is `20210529010844`, 27 seconds later. Verify this dependency and record a resource-specific same-crawl compatibility decision. Do not reject it solely for being later, and do not use it as justification to approve every later resource. Inspect all `needs_review` resources individually; add a per-resource approval mechanism if the current global `--allow-later` option is too broad.

Keep original font-family declarations and their provenance, but retain the project's no-font-binary redistribution policy. Do not copy system/tool-environment fonts or repackage font files. Use documented system fallbacks where necessary and report the resulting typography difference. Preserve original JS references as research metadata when useful; never run unknown archived scripts to make the site work.

### Fill blog, external-source, shop and media gaps

Follow the two known blog offsets and the third-listing lead; independently enumerate individual articles so a broken pagination page does not end the crawl. Preserve exact slugs, publication dates, credits, captions, authors/tags, reblog/source links and titleless entries. Avoid inventing dates or titles from the checklist's descriptive labels. Investigate the two additional observed article paths:

```text
/blog/bringing-back-the-og-t-shirt-in-green-and-gold-if
/blog/el-primer-d-a-de-clase
```

Treat the 30 external destinations as bounded, source-linked investigations. Recover only the relevant article/image evidence, not entire third-party websites. Current live pages may help corroborate metadata but are not automatically historical substitutes; document any non-archive fallback and never let a live-site fetch silently overwrite a historical source.

Find a valid Shop capture or its evidence-backed historical destination. Render recovered products/read-only catalog information without checkout or current inventory claims. Never present a captured provider error as the reconstructed shop.

Preserve the 11 original YouTube IDs and their order, titles only where supported, and the SoundCloud leads (track `87129356` and `prometheusbrown/racist-accident`). An embed/player page or title is not a recovered video/audio file. Do not bypass provider access controls or DRM. Use local presentation plus explicit external viewing/listening links as the default. Optional click-to-load players must be intentional, clearly external, and tested separately; no automatic third-party requests. Never manufacture missing media.

### Network limits and resume behavior

Use a descriptive User-Agent, modest request pacing, bounded retries, backoff and `Retry-After`. Avoid broad parallel hammering. Preserve successes and checkpoints through interruption. Do not bypass archive blocks or access controls.

If this environment cannot reach the archive, diagnose the actual error briefly, then use an authorized GitHub Actions recovery run if available. Read and verify the workflow first. Watch the run, download its artifact into a **staging directory**, inspect paths/content and deliberately merge checkpoints/raw files; do not blindly overwrite local work. Resume a specific prior run through `resume_run` rather than starting every runner from zero. Save valuable recovery data durably rather than relying solely on expiring workflow artifacts.

A dispatched workflow is not a finished crawl. When permissions or network access prevent progress, still complete feasible code/tests and write exact recovery/resume instructions. Clearly identify the blocker and unfinished coverage; do not turn synthetic fixtures or placeholder pages into claimed recovered content.

## Workstream 3: produce a faithful self-contained static site

Use recovered markup/classes, original CSS and real imagery as the starting point. Match the selected homepage's logo, navigation, typography as permitted, spacing, backgrounds, image sizing/crop and desktop layout before adding speculative polish. This is **preservation, not a redesign**: no newly invented hero section, marketing copy, cards, gradients or UI framework.

Repair only the behavior that originally depended on Squarespace or scripts, using minimal local code. Audit the current sanitizer/builder against actual responses: it may need changes for menus, CSS dependencies, hidden/lazy content, image sizing, gallery behavior, or unfamiliar archive markup. Do not weaken safety checks merely to make a test pass. Add regressions around real recovered input, with appropriately small fixtures.

Preserve the homepage, Blog, Shows, Video, Shop, Holler, discovered articles, pagination, and relevant author/tag navigation. Map query-based pages to real static paths and maintain tested legacy query handling. Preserve historical spelling in paths/tags, including the observed `Blue+Schoalrs` query. Choose deterministic output paths without collisions or directory traversal. Test relative, absolute, encoded, fragment and trailing-slash links under both `/` and `/bluescholars/`.

Remove Wayback toolbars/injection, original tracking, obsolete forms, commerce actions, and unsafe scripts. Keep forms disabled and historical contact/show information clearly historical. Make media links honest about external playback. All ordinary rendering assets must be local; no runtime requests to Wayback, Squarespace, Tumblr, remote stylesheets, analytics or font services. Preserve an appropriate content security policy.

Do not fill holes with fabricated content, generated photographs, unrelated stock images, or copied text from an unrelated era. Put remaining limitations in a restrained archive-status page/notice with per-resource evidence; do not let diagnostic styling replace the original design. Separate older incompatible-era history from the reference presentation, but retain it in the source catalog and an appropriate historical section where practical.

Keep acquisition, unreviewed candidate output, reviewed-source promotion and release output separate. Builds must be deterministic and work offline from reviewed local sources. A routine Pages build must not need a new archive crawl.

## Workstream 4: verification, review and conditional deployment

Run all tests, add coverage for actual fixes and inspect build/check results. Useful existing commands:

```bash
python -m pytest -q
python -m compileall -q restore tests
bash -n scripts/create-github-repo.sh scripts/enable-pages.sh
python -m restore build --candidate --base-path /bluescholars
python -m restore check --candidate --base-path /bluescholars
```

Also test reviewed builds at the domain root and project subpath after sources are legitimately promoted. A placeholder build passing a link checker is not a release.

Use an available real browser/Playwright for reference/local comparisons and save screenshots plus a short comparison report. Suggested widths are 1440, 768 and 390 pixels; compare a matching archived view when it is available, and test narrow-screen usability without redesigning the site. Inspect homepage, at least both blog listings and an article, plus Shows, Video, Holler and Shop status. Check navigation, image crop/order, overflow, console errors, redirects, missing resources and keyboard accessibility. Use network logs and an offline/intercepted-network test to prove ordinary rendering is not loading remote dependencies. This prompt authorizes **agent-performed** visual review; record that provenance, not a fictitious human review.

Before a release, require all of the following:

- Genuine recovered homepage HTML, original styling or explicitly documented evidence-based repairs, and recovered principal homepage imagery—not a placeholder-only homepage.
- Core navigation works. Unrecovered historical sections are truthfully explained rather than hidden or called complete.
- Tests and root/subpath build/link/resource checks pass; no unexplained critical browser errors or automatically loaded remote dependencies.
- A recorded visual comparison supports the fidelity claimed. Unavailable reference rendering is a limitation, not a passed comparison.
- Every included later capture has a documented compatibility decision; publication state reflects the sources actually reviewed.
- Source counts, raw-file hashes, known gaps and archive-index coverage are reported accurately.

Do not set review flags merely to bypass gates. The supplied approval command currently writes an owner-review note; if using delegated agent review, correct/extend that metadata and its tests so it truthfully records the actor and evidence. Keep publication authorization (this prompt), agent inspection, and actual site verification distinct. Do not claim a human viewed screenshots when only the agent did.

Preserve attribution and the project's rights notice. Archive availability does not establish a redistribution license. Record unresolved rights questions and do not label third-party content as newly owned or broadly licensed. Use a nonintrusive historical-restoration notice rather than suggesting this is the current official band site.

### GitHub execution

Check `gh auth status`, the authenticated login, and whether `keithah/bluescholars` actually exists. Distinguish missing repository from insufficient permissions. Do not create the project under another account silently. Read `scripts/create-github-repo.sh` before using it: it assumes no existing origin/repository and dispatches recovery after pushing. If the repository exists, use a safe compatible workflow rather than rerunning a creation script that will refuse or replacing remote history. Keep commits scoped and do not push unrelated local changes.

Validate workflow syntax and current official GitHub guidance as needed; old documentation in this handoff is not proof that a dependency/action version remains suitable. Use least-privilege workflow permissions and no secrets in logs or source control. Do not enable scheduled crawls or billable infrastructure.

After the release gates genuinely pass, promote the inspected sources, record truthful approval metadata, commit/push, enable Pages for the intended project, and dispatch the manual Pages workflow with its explicit publish confirmation. Use its reported deployment URL. Verify the actual live homepage, a nested article, assets, a pagination route, and a 404; check for project-subpath failures. Do not report a deployment complete merely because a workflow was started.

If visual inspection, authentication, meaningful recovery, or another release condition remains blocked, withhold publication. Preserve the usable work and state, and specify the exact remaining action. Do not publish the current diagnostic/empty-source scaffold as the restoration.

## Required handoff at the end

Update documentation from observed results, not optimistic estimates. Deliver:

1. The repository/branch/commit actually created or updated, or the precise GitHub blocker.
2. A functioning offline static build with as much verified original content as could be recovered, plus repeatable build/recovery commands.
3. A machine-readable recovery/provenance manifest and gap report. Separate discovered URLs, attempted URLs, validated downloaded files, unique hashes, recovered pages, remaining placeholders, and later-capture exceptions. Report capture-index coverage independently.
4. A concise visual/completeness report, screenshots when obtained, test results and live deployment checks when applicable.
5. Durable source/checkpoint storage and safe resume instructions. Keep generated transient caches, virtual environments, credentials, huge unrelated archives and font binaries out of the repository.
6. The verified Pages URL if published; otherwise a clear explanation that it was not deployed and the exact failed gate.
7. A portable final source/site ZIP where the environment allows, excluding secrets, fonts and development caches; include the reports and instructions needed to reproduce the result.

Do the work now. Prioritize actual content recovery and a verified faithful site over expanding planning documents. Continue through recoverable errors, preserve checkpoints, and report remaining uncertainty honestly.
