# Blue Scholars historical website archive

This repository is reconstructing three archived versions of **bluescholars.com** as a self-contained static site:

- `/2007/` — the older early design
- `/2009/` — the WordPress-era site, whose captures continue through 2013
- `/2013/` — the Squarespace design, first located in September 2013; the last intact homepage capture located so far is September 30, 2023
- `/lj/` — a separate archive for the separately hosted Blue Scholars LiveJournal; it is not presented as another official website design
- `/prometheusbrown/` and `/sabzi/` — separate archives for the related artist sites, each with its own dated edition pages and source provenance

The root page is an edition gateway. The visual baseline for the Squarespace edition is the May 29, 2021 homepage capture. Original source bytes, capture dates, hashes, and archive provenance are retained separately from the rendered output.

## Current status

The target public repository is [keithah/bluescholars](https://github.com/keithah/bluescholars), on `main`. A user-requested public candidate preview is live at [keithah.github.io/bluescholars](https://keithah.github.io/bluescholars/); its static snapshot is on the separate `gh-pages` branch. This is an incomplete, unreviewed preview—not a finished restoration. The publication flags in `source/review.json` remain false, and the reviewed-release workflow remains gated.

Recovery has reached the static reconstruction stage, but it is incomplete. The Wayback domain index is complete in the saved checkpoint; the current candidate build has substantial explicit gaps. Independent copies have also been recovered from Common Crawl and Arquivo.pt. See the current [recovery report](docs/recovery-report/RECOVERY_REPORT.md), [gap report](docs/recovery-report/GAP_REPORT.md), [verification record](docs/VERIFICATION.md), and [work log](docs/WORK_LOG.md) for exact counts and remaining work.

The artist-site expansion has indexed 1,580 Wayback rows for `prometheusbrown.com` and 322 for `sabzi.co`. The observed Prometheus Brown site generations include its 2008 film blog, 2009 and 2010 WordPress blog snapshots, 2013/2016 portfolio captures, and 2019/2022 Squarespace captures. Sabzi has 2013, 2016, 2019 and 2022 Squarespace snapshots. The current candidate renders 615 captured pages and 381 local assets across these 11 editions. Those sources remain candidate-only; 205 later-page captures need compatibility review, eight unsafe SVG files are withheld from rendered output, and many linked pages, original stylesheets and images remain unavailable. The 2009 Prometheus Brown numeric HTML set includes spam-injected captures; eight unique 2024 homepage captures were inspected and contain JAYA77 casino spam, so they are excluded from the site editions.

See the per-capture [artist-site recovery report](docs/recovery-report/artist-sites-report.md) for the acquisition counts, source dates and current gaps.

## Preview and tests

Python 3.11 or newer is supported. From the project directory:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m restore build --candidate
python -m restore check --candidate
python -m restore serve --candidate
```

Open `http://127.0.0.1:8080/`. Candidate output includes unreviewed downloaded sources and is never a release. Test the project Pages prefix separately:

```bash
python -m restore build --candidate --base-path /bluescholars
python -m restore check --candidate --base-path /bluescholars
python -m restore serve --candidate --base-path /bluescholars
```

## Resume archive recovery

The manually dispatched **Recover Internet Archive sources** workflow stores resumable checkpoints and raw payloads as an artifact. It can continue from a prior run and query the three editions separately. It also runs bounded exact-URL searches for the 42 documented source-linked image URLs, queries independent Common Crawl and Arquivo.pt archives, and never publishes the site.

The large Blue Scholars crawl checkpoints under `recovery/state.json`, `recovery/raw/` and `recovery/index/` are excluded from Git. The smaller `recovery/artist-sites/` index, manifest and hashed captures are tracked as a resumable source collection. To resume the main-site crawl from a workflow artifact, download it into a staging directory, inspect its contents, then merge its state and raw files deliberately. See the recovery report for the latest saved run IDs and exact commands.

For local archive access, the main commands are:

```bash
python -m restore index --max-pages 20
python -m restore index-assets --max-assets 100 --max-pages 3
python -m restore recover --max-files 500 --retry-failed
python -m restore capture-era --era 2007 --max-files 2000
python -m restore capture-era --era 2009 --max-files 2000
python -m restore capture-era --era 2013 --max-files 2000
python -m restore commoncrawl --max-records 1800 --workers 4
python -m restore arquivo --history-url bluescholars.com
python -m restore artist-index
python -m restore artist-recover --max-files 1800
```

These commands preserve dated variants and provenance. A saved capture is not automatically a compatible or publishable source. Promotion verifies hashes; later captures remain individually review-gated.

## Publication gate

The normal static output uses only `source/catalog.json` and `source/raw/`; it does not depend on Wayback or remote asset hosts for ordinary rendering. Forms and embedded media are handled as historical references instead of active third-party services. The reviewed release build still requires reviewed source bytes, accurate gap reporting, a successful visual comparison, root and `/bluescholars/` checks, and explicit publication approval. The current Pages deployment is a clearly marked candidate preview requested by the owner; it does not satisfy or change those release gates. No custom domain or DNS change is part of this project.
