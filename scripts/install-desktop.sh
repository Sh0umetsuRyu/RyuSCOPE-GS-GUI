#!/usr/bin/env bash
# Installs a per-user .desktop entry. Never needs sudo. No game folders are copied.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ ! -f "$ROOT/main.py" ]]; then
  echo "Missing main.py: merge this kit into your actual v0.5.2 source first." >&2; exit 2
fi
ICON="$ROOT/assets/ryuscope-emblem.png"
[[ -f "$ICON" ]] || { echo "Icon missing: $ICON" >&2; exit 2; }
APP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
mkdir -p "$APP_DIR"
# Escape desktop Exec arguments according to freedesktop quoting rules.
quote_desktop_arg() { local v="$1"; v="${v//\\/\\\\}"; v="${v//\"/\\\"}"; v="${v//\$/\\$}"; v="${v//\`/\\\`}"; printf '"%s"' "$v"; }
EXEC_ARG="$(quote_desktop_arg "$ROOT/scripts/run-local.sh")"
cat > "$APP_DIR/ryuscope-gs.desktop" <<EOF
[Desktop Entry]
Type=Application
Version=1.0
Name=RyuSCOPE GS
Comment=Gamescope launcher for native Linux and Steam/Proton games
Exec=$EXEC_ARG
Icon=$ICON
Terminal=false
Categories=Game;Utility;
StartupNotify=true
EOF
chmod 644 "$APP_DIR/ryuscope-gs.desktop"
echo "Installed RyuSCOPE GS desktop entry: $APP_DIR/ryuscope-gs.desktop"
echo "Open it from your desktop environment's application launcher."
