#!/usr/bin/env bash
# Creates a PUBLIC repo from this project and starts recovery, never Pages deployment.
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
REPO="keithah/bluescholars"
command -v gh >/dev/null || { echo 'Install GitHub CLI and run gh auth login first.' >&2; exit 1; }
command -v git >/dev/null || { echo 'Git is required.' >&2; exit 1; }
gh auth status >/dev/null
LOGIN="$(gh api user --jq '.login')"
[[ "$LOGIN" == 'keithah' ]] || { echo "Authenticated as $LOGIN, not keithah. Switch accounts first." >&2; exit 1; }
if gh repo view "$REPO" >/dev/null 2>&1; then
  echo "$REPO already exists; nothing has been overwritten. Push/import into it deliberately." >&2
  exit 1
fi
[[ -f restore/__main__.py && -f source/review.json ]] || { echo 'Not the restoration project.' >&2; exit 1; }
if [[ ! -d .git ]]; then git init -b main; fi
[[ "$(git rev-parse --show-toplevel)" == "$ROOT" ]] || { echo 'Unexpected Git root.' >&2; exit 1; }
if git remote get-url origin >/dev/null 2>&1; then
  echo 'An origin remote already exists. Refusing to change it automatically.' >&2; exit 1
fi
git config user.name >/dev/null || { echo 'Set git config user.name before creating the initial commit.' >&2; exit 1; }
git config user.email >/dev/null || { echo 'Set git config user.email before creating the initial commit.' >&2; exit 1; }
git add .
if ! git diff --cached --quiet; then git commit -m 'Initialize Blue Scholars archive restoration'; fi
git branch -M main
gh repo create "$REPO" --public --source=. --remote=origin --push \
  --description 'Historical bluescholars.com restoration from the Internet Archive; static GitHub Pages build'
echo "Created $REPO. Starting the manual archive recovery workflow."
for attempt in 1 2 3; do
  if gh workflow run recover.yml --repo "$REPO" --ref main; then
    echo 'Recovery queued. Run: gh run list --repo keithah/bluescholars --workflow recover.yml'
    echo 'Nothing has been published to GitHub Pages.'
    exit 0
  fi
  sleep 5
done
echo 'Repository created, but automatic workflow dispatch failed. Retry: gh workflow run recover.yml --repo keithah/bluescholars' >&2
exit 1
