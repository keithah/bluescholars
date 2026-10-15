# Blue Scholars Recovery and Static Build Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement task-by-task.

**Goal:** Produce a resumable archive recovery tool and an offline, review-gated static build for bluescholars.com.

**Architecture:** Acquisition saves untouched source responses and provenance; a separate deterministic builder sanitizes and localizes reviewed source. A diagnostic preview distinguishes unavailable material from restored pages. Recovery never deploys.

**Tech Stack:** Python 3.11+, requests, Beautiful Soup, tinycss2, pytest, GitHub Actions/Pages.

**Spec:** `docs/superpowers/specs/2026-10-15-restoration.md`.

## Global constraints

Use capture 20210529010817 as baseline. Preserve alternate captures and query identity. No invented historical material. No font files in the deliverable. No runtime archive/Squarespace dependencies. Do not publish until visual/content review. Support root and `/bluescholars` paths. Do not change DNS.

## Review focus

- Truncated CDX results must not report complete coverage.
- A 200 response containing a provider error must not become recovered content.
- Relative/CSS URLs and pagination must survive subpath deployment.
- Crawled scripts, forms, redirects and remote assets must not execute in output.
- Failed/interrupted runs must retain provenance and resume without redownloading successes.

## Task 1: URLs, discovery, and persistent state

Files: `restore/urls.py`, `restore/discover.py`, `restore/state.py`, `tests/test_core.py`.
Interfaces: `original_url(value, base='') -> str`; `route(url) -> str`; `discover_html(text, url) -> list[dict]`; `discover_css(text,url) -> list[str]`; `State(root)` with `add`, `save` and `data`.

- [x] Test archive wrappers, encoded schemes, offsets, unsafe paths, CSS imports, lazy images, third-party crawl boundaries, and checkpoint persistence.
- [x] Run pytest and observe missing implementations.
- [x] Implement pure functions and atomic JSON state saves.
- [x] Run the full test suite, then commit.

## Task 2: Archive acquisition

Files: `restore/archive.py`, `restore/recover.py`, `tests/test_recovery.py`.
Interfaces: `parse_cdx(text) -> (rows,resume_key)`; `validate_payload(body,kind) -> None`; `ArchiveClient.get(url) -> Payload`; `index(state,client,max_pages)`; `recover(state,client,max_files)`.

- [x] Test resumable CDX pagination, alternate capture ranking, error-body rejection, retry delays, redirect confinement, successful-download checkpoints and after-reference quarantine.
- [x] Run tests to observe the new cases failing.
- [x] Implement bounded, paced acquisition; persist raw bytes, SHA256, actual capture and every result. Skip fonts, scripts and third-party media binaries.
- [x] Run the full suite and commit.

## Task 3: Static renderer and validation

Files: `restore/render.py`, `restore/build.py`, `restore/check.py`, `tests/test_build.py`, `public/archive-ui.css`.
Interfaces: `render_html(text,url,resources,base) -> (html,issues)`; `build(root,output,base,candidate=False,release=False) -> report`; `check(output,base) -> errors`.

- [x] Test local assets, CSS URLs/imports, malicious URLs, no scripts/forms/remote loads, pagination, missing-content placeholders, root/subpath builds, publication gates and deep links.
- [x] Run tests to observe failures.
- [x] Preserve original markup/classes; localize dependency URLs; add separate recovery notices. Add an offline diagnostics page without presenting it as restored visual design.
- [x] Validate both output roots; commit.

## Task 4: CLI, GitHub setup and workflows

Files: `restore/__main__.py`, `scripts/create-github-repo.sh`, `scripts/enable-pages.sh`, `.github/workflows/*.yml`, `README.md`, `tests/test_cli.py`.

- [x] Test CLI help/seed/build/check, zero-content release rejection, and workflow publication guards.
- [x] Implement commands, separate manual recovery/artifact workflow and explicitly reviewed Pages deployment. Include authenticated CLI repo setup for `keithah/bluescholars`.
- [x] Run all tests, compile checks, shell syntax checks and real offline preview builds. Self-review code and package repository with verification report.

## Execution notes

Continue in this session per the user's instruction. The connected GitHub action set lacks repository creation; `keithah/bluescholars` returned 404. Build a new isolated local repository rather than write to an unrelated project. Network DNS fails in the execution environment; live end-to-end recovery must be tested elsewhere. Do not mark that as a successful crawl.

## Completion boundary

The checked tasks describe implemented and offline-tested recovery/build tooling. They do not indicate successful live acquisition, remote repository creation, GitHub workflow execution, deployment, or historical visual fidelity. See `docs/VERIFICATION.md`.
