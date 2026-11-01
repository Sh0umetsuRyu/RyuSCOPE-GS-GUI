#!/usr/bin/env bash
# Creates local Python .venv and installs the requirements declared by the real app.
# Never uses sudo, changes system packages, or touches Steam.
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ ! -f main.py ]]; then
  printf 'RyuSCOPE app source missing: main.py not found. This is a documentation-only starter until v0.5.2 source is imported.\n' >&2
  exit 2
fi
if [[ ! -f requirements.txt ]]; then
  printf 'No verified requirements.txt found. Maintainer must supply dependencies from the actual v0.5.2 source before installing.\n' >&2
  exit 2
fi
if ! command -v python3 >/dev/null 2>&1; then
  printf 'python3 is not installed. Follow your distribution official packaging guidance.\n' >&2
  exit 2
fi
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
printf '\nPython environment ready. Next: bash scripts/run-local.sh\n'
