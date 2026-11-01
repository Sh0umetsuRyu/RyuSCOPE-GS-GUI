#!/usr/bin/env bash
# Read-only environmental availability report. No sudo, no changes to disk/game data.
set -u
cd "$(dirname "$0")/.."
printf 'RyuSCOPE GS v0.5.2: environment check (read-only)\n'
printf '%s\n' '----------------------------------------------'
for tool in bash python3 gamescope steam git; do
  if command -v "$tool" >/dev/null 2>&1; then
    printf '[found] %-11s %s\n' "$tool" "$(command -v "$tool")"
  else
    printf '[missing] %s\n' "$tool"
  fi
done
for tool in mangoapp gamemoderun; do
  if command -v "$tool" >/dev/null 2>&1; then
    printf '[optional found] %s\n' "$tool"
  else
    printf '[optional missing] %s (not required for v0.5.2 core launch)\n' "$tool"
  fi
done
printf '\n'
if command -v python3 >/dev/null 2>&1; then python3 --version 2>&1; fi
if command -v gamescope >/dev/null 2>&1; then
  printf 'Gamescope executable: present. Check its version separately if needed.\n'
fi
printf '\nLocal app files:\n'
for file in main.py requirements.txt; do
  if [[ -f "$file" ]]; then printf '[found] %s\n' "$file"; else printf '[missing] %s (required before this is a runnable application)\n' "$file"; fi
done
printf '\nThis check did not install anything or modify Steam.\n'
