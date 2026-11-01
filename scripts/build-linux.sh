#!/usr/bin/env bash
# Bundle the verified local Python source using PyInstaller on a Linux host.
# For matching glibc/Qt compatibility, build on your oldest target distribution.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
[[ -f main.py ]] || { echo 'Missing main.py: merge original v0.5.2 source first.' >&2; exit 2; }
[[ -f requirements.txt ]] || { echo 'Missing verified requirements.txt: do not guess application dependencies.' >&2; exit 2; }
[[ -f assets/ryuscope-emblem.png ]] || { echo 'Missing emblem.' >&2; exit 2; }
[[ -x .venv/bin/python ]] || { echo 'Run bash scripts/setup-python.sh first.' >&2; exit 2; }
.venv/bin/python -m PyInstaller --version >/dev/null 2>&1 || {
  echo 'PyInstaller is not installed in .venv. Run .venv/bin/python -m pip install pyinstaller and retry.' >&2; exit 2;
}
# Using onedir makes dependencies easier to inspect and debug than onefile.
.venv/bin/python -m PyInstaller --noconfirm --clean --onedir --windowed \
  --name RyuSCOPE-GS --add-data 'assets/ryuscope-emblem.png:assets' main.py
printf '\nBundled binary: %s/dist/RyuSCOPE-GS/RyuSCOPE-GS\n' "$ROOT"
printf 'Bundling Python does NOT bundle host Gamescope, Steam, Proton, GPU drivers, or MangoHud.\n'
