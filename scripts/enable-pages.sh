#!/usr/bin/env bash
# Explicitly configure this new project's Pages source. Does not deploy or change DNS.
set -euo pipefail
REPO='keithah/bluescholars'
command -v gh >/dev/null || { echo 'GitHub CLI is required.' >&2; exit 1; }
gh auth status >/dev/null
if gh api "repos/$REPO/pages" >/dev/null 2>&1; then
  gh api --method PUT "repos/$REPO/pages" -f build_type=workflow
else
  gh api --method POST "repos/$REPO/pages" -f build_type=workflow
fi
echo 'Pages configured. Deployment still requires source review and a confirmed pages.yml run.'
