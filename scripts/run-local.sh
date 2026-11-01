#!/usr/bin/env bash
# Launch original v0.5.2 source, keeping Python imports relative to the project.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
[[ -f main.py ]] || { echo 'main.py missing; merge your real v0.5.2 source first.' >&2; exit 2; }
if [[ -x .venv/bin/python ]]; then
  exec .venv/bin/python main.py "$@"
elif command -v python3 >/dev/null 2>&1; then
  exec python3 main.py "$@"
else
  echo 'Python 3 missing.' >&2; exit 2
fi
