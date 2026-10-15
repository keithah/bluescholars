# Blue Scholars — static archive restoration

Restore the historical **bluescholars.com** site using the **May 29, 2021** homepage as the visual baseline, with other capture dates supplying missing material. The output is ordinary HTML/CSS/images for GitHub Pages, not a replacement Squarespace installation.

## Current status

**The recovery/build tooling is implemented; the historical website is not yet recovered.**

This project contains the archive recovery and static build tools. Recovery is now running against the live Internet Archive from both the local workspace and the manual GitHub Actions workflow. See [the work log](docs/WORK_LOG.md) and the generated provenance reports for current results. Until original homepage markup, styling and imagery have been inspected and reviewed, any preview remains a recovery candidate rather than a released restoration.

The remote `keithah/bluescholars` repository was **not created**: the connected GitHub interface did not expose repository creation. The setup script below performs that operation from an authenticated terminal. Neither it nor the recovery workflow publishes the site.

## Create the GitHub repository and start recovery

Prerequisites: Git, GitHub CLI (`gh`), an authenticated `keithah` account, and configured Git name/email. Run `gh auth login` through GitHub CLI when authentication is needed; do not put a token in this project.

From this extracted project folder:

```bash
bash scripts/create-github-repo.sh
```

The script initializes the packaged project on `main`, creates the **public** `keithah/bluescholars` repository, pushes the files, and dispatches the recovery workflow. It refuses to overwrite an existing remote repository or an existing `origin`. It does not enable Pages or change DNS. A partial failure is reported rather than hidden; for example, repository creation can succeed while workflow dispatch fails.

Inspect the job:

```bash
gh run list --repo keithah/bluescholars --workflow recover.yml
```

GitHub authentication must permit repository creation, pushing workflow files, and workflow dispatch. These remote operations have not been tested from the preparation environment.

## Local setup and preview

Python 3.11 or newer is required. Python 3.13 was used for verification. Node.js is needed only for the JavaScript regression test, not for recovery, building, or hosting.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m restore seed
python -m restore build
python -m restore check
python -m restore serve
```

Open `http://127.0.0.1:8080/`. The preview server binds only to localhost. With no recovered source collection, this is an honest recovery-status preview, not a visually restored site.

For the GitHub project subpath:

```bash
python -m restore build --base-path /bluescholars
python -m restore check --base-path /bluescholars
python -m restore serve --base-path /bluescholars
```

The included server handles the project subpath. A generic server pointed at `_site` does not automatically mount it at `/bluescholars`.

## Recover sources on a machine with working archive access

```bash
python -m restore seed
python -m restore index --max-pages 20
python -m restore recover --max-files 150
python -m restore status
```

`index` inventories the domain, including subdomains, without collapsing away alternative captures. Each CDX batch requests up to 500 records. A limit or interrupted query leaves a continuation cursor; run the same command again to resume. `index_complete: false` is not complete coverage. It also does not mean no captures exist.

`recover` can start from the known seed URLs even if CDX fails. It follows internal pages, stylesheet dependencies and image references, tries alternate captures, and records the **actual resolved capture date**, source URL, SHA256, byte count and each attempt. The reference capture and compatible earlier captures are preferred. Responses that resolve after the reference are saved as `needs_review`, not automatically published.

Stylesheets and homepage assets are prioritized ahead of the blog backlog. The downloader only makes requests to Wayback; it does not fall back silently to today's live site. It refuses redirects outside the archive, limits response sizes, honors Retry-After and paces requests. Font files, original JavaScript, third-party video/audio binaries and unsupported downloads are excluded and tracked. External websites are not recursively mirrored.

Resume more of the crawl and retry unresolved URLs:

```bash
python -m restore index --max-pages 50
python -m restore recover --max-files 500 --retry-failed
```

Target a source-linked missing asset or path in the index:

```bash
python -m restore index --url 'https://example-cdn.invalid/exact-observed-image.jpg' --match exact
```

Replace the example with an actual observed source URL. Do not guess that a similar filename is the same image. Additional verified URLs/capture hints can be entered in `recovery/seeds/inventory.json` and loaded with `seed`.

## Recover using GitHub Actions

The **Recover Internet Archive sources** workflow is manually dispatched and has no publishing permission. Its `archive-recovery` artifact includes the raw responses, checkpoint, capture-index batches, report and candidate preview. Artifacts are configured for 30-day retention; save important recovered sources rather than relying on artifact storage indefinitely.

Download a completed or partially failed run into this project:

```bash
gh run download RUN_ID --repo keithah/bluescholars --name archive-recovery --dir .
python -m restore build --candidate
python -m restore check --candidate
python -m restore serve --candidate
```

Resume that checkpoint in a new runner:

```bash
gh workflow run recover.yml --repo keithah/bluescholars \
  -f resume_run=RUN_ID -f max_files=500 -f max_index_pages=50
```

Use the numeric run ID printed by GitHub. Each new run otherwise starts from the repository's seed inventory; runner disks are not persistent. Failed runs still attempt to save their checkpoint and report. A forced runner termination can interrupt the artifact upload, so retain the previous checkpoint too.

## Inspect, promote, then publish

Acquisition and publication are separate. `_candidate` is for unreviewed downloads. The normal `_site` build consumes only `source/catalog.json` and its promoted raw files.

After inspecting the candidate and capture dates:

```bash
python -m restore promote --reviewed
python -m restore build --base-path /bluescholars
python -m restore check --base-path /bluescholars
python -m restore serve --base-path /bluescholars
```

Promotion verifies source hashes and copies only reviewed responses into `source/raw`. Later captures require a separate compatibility decision for each resource. Record one only after inspecting that resource:

```bash
python -m restore compatibility-review --url 'EXACT_ORIGINAL_URL' --reason 'Resource-specific evidence for historical compatibility.'
python -m restore promote --reviewed
```

The decision records the reviewing actor, capture, hash and evidence note. The former global `--allow-later` switch is rejected because it could approve unrelated later redesigns at once.

Compare desktop and mobile renderings with the archived reference. Check the logo, typography, spacing, image sizes/order, article text and dates, blog pagination, historical contact/shop behavior and all reported gaps. The renderer preserves original markup/classes and localizes available assets, but removing Squarespace runtime behavior can still require targeted visual repairs. Fonts are not bundled; any typography fallback remains a known fidelity issue. Preservation of original credits does not establish a license to republish; review rights separately.

Only after this review:

```bash
python -m restore approve --visual-reviewed --publish-approved
git add source
git commit -m 'Approve reviewed historical sources for publication'
git push
bash scripts/enable-pages.sh
gh workflow run pages.yml --repo keithah/bluescholars -f confirm_publish=true
```

The Pages workflow requires both stored review approval and an explicit confirmation, runs the tests, builds in `--release` mode, checks local dependencies, and uploads only `_site`. A release build also requires original homepage HTML and recovered CSS. The current empty source collection deliberately cannot pass that gate.

No custom domain or CNAME is configured. The anticipated project URL after a successful deployment is `https://keithah.github.io/bluescholars/`; it is not a live deployment claim. Verify the URL reported by the actual successful Pages run.

## What the static conversion does

It strips the archive toolbar, original scripts, event handlers and tracking/preload tags; localizes recovered HTML/CSS image dependencies; turns lazy-loaded images into ordinary local images; converts known blog offsets into real directory pages; adds minimal local pagination JavaScript and script-free navigation; and emits explicit placeholders for unavailable pages/images.

Forms are disabled. YouTube and other media become ordinary external links instead of automatically loading third-party players. Historical shop/contact content is not a current commerce or support service. A Content Security Policy prevents automatic connections to the archive, Squarespace or external media providers. Old scripts are not executed merely because they were archived.

The offline checker distinguishes navigational external links from automatic resource loads. Passing it establishes local link/resource consistency, not historical completeness, pixel equivalence, current video playback, or that every potential archive capture has been found.

## Repository structure

```text
restore/                 Recovery, rendering, validation and CLI
recovery/seeds/           Verified reconnaissance references from the handoff
recovery/state.json      Resumable crawl checkpoint (generated, ignored)
recovery/raw/            Untouched acquired bytes (generated, ignored)
recovery/index/          Raw CDX batches (generated, ignored)
source/catalog.json      Reviewed-source manifest
source/raw/              Promoted source bytes (commit after review)
source/review.json        Explicit visual/publication approval
public/archive-ui.css    Restoration notices and diagnostic pages only
_site/                   Generated reviewed static output (ignored)
_candidate/              Generated unreviewed candidate output (ignored)
scripts/                 Explicit authenticated GitHub setup
.github/workflows/       CI, manual recovery, manual publication
tests/                   Offline automated tests and regression fixtures
docs/                    Design, plan, verification and known limitations
```

## Technical references

- Reference capture: https://web.archive.org/web/20210529010817/http://bluescholars.com/
- Original blog reference: https://web.archive.org/web/20190719224039/http://bluescholars.com/blog
- CDX API, including resume keys: https://github.com/internetarchive/wayback/tree/master/wayback-cdx-server
- GitHub CLI repository creation: https://cli.github.com/manual/gh_repo_create
- GitHub custom Pages workflows: https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages
- Pages REST API: https://docs.github.com/en/rest/pages/pages

Action major versions were selected from official documentation during preparation. Direct Python dependency versions match the verified local environment. No claim is made that the source crawl or GitHub workflows have executed successfully online yet.
