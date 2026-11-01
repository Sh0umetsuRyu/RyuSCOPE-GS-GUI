#!/usr/bin/env bash
# Read-only leak scanner of Python source. Manual review still required.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
echo '=== Personal absolute paths embedded in Python sources ==='
if ! find . \( -name .git -o -name .venv -o -name build -o -name dist \) -prune -o -name '*.py' -print0 \
  | xargs -0 -r grep -nE '(/home/[A-Za-z0-9_.-]+/|/mnt/[A-Za-z0-9_.-]+/|[A-Z]:\\\\Users\\\\)' ; then
  echo 'No obvious personal absolute paths detected in Python source.'
else
  echo 'Review every match. Some sample paths may be intentional documentation.'
fi
echo '=== Check for application source ==='
[[ -f main.py ]] && echo 'main.py found' || echo 'main.py not present: this is NOT a runnable release'
echo '=== File/folder review ==='
find . -maxdepth 2 -type d ! -path '*/.git*' ! -path '*/.venv*' | sort
