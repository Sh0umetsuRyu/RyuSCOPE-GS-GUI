#!/usr/bin/env bash
# Read-only local preflight. Does NOT scan file contents for secrets.
set -euo pipefail
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  printf 'Not inside a Git repository. Run git init in your project directory first.\n' >&2
  exit 1
fi
printf '== Candidate files (not ignored) ==\n'
git ls-files --cached --others --exclude-standard
printf '\n== Files staged for commit ==\n'
git diff --cached --name-only
printf '\n== Possible risk paths (tracked or untracked, regardless of ignores) ==\n'
find . \( -name .git -o -name .venv -o -name venv \) -prune -o \
  \( -iname '*.env' -o -name '.env' -o -name 'compatdata' -o -name 'steamapps' -o -name 'pfx' -o -name 'userdata' -o -name 'user_data' -o -iname '*token*' -o -iname '*secret*' \) -print
printf '\nReview candidate files and inspect sources for hardcoded paths/tokens before committing.\n'
