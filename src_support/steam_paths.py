"""Read-only, user-portable Steam library/path utilities for integration into RyuSCOPE.

Nothing here assumes a particular person's home directory or storage mount.
Use the GUI directory picker to add extra Steam libraries via save_library().
This module does NOT automatically change main.py; wire it into the original source
only after regression tests.
"""
from __future__ import annotations
import json
import os
import re
from pathlib import Path

APP_NAME = "ryuscope-gs"


def settings_file() -> Path:
    base = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))).expanduser()
    return base / APP_NAME / "user-libraries.json"


def load_user_libraries() -> list[Path]:
    try:
        data = json.loads(settings_file().read_text(encoding="utf-8"))
        items = data.get("steam_library_paths", [])
        if not isinstance(items, list):
            return []
        return _unique_paths(items)
    except (FileNotFoundError, ValueError, OSError, TypeError):
        return []


def _unique_paths(items) -> list[Path]:
    seen: set[str] = set()
    result = []
    for item in items:
        if not isinstance(item, str) or not item.strip():
            continue
        path = Path(item).expanduser().resolve(strict=False)
        key = str(path)
        if key not in seen:
            seen.add(key)
            result.append(path)
    return result


def save_library(path: str | Path) -> Path:
    selected = Path(path).expanduser().resolve(strict=True)
    # The user may select the Steam library root or its steamapps directory.
    if selected.name == "steamapps":
        selected = selected.parent
    if not (selected / "steamapps").is_dir():
        raise ValueError("Selected folder is not a Steam library (steamapps missing).")
    libraries = _unique_paths([*(str(p) for p in load_user_libraries()), str(selected)])
    destination = settings_file()
    destination.parent.mkdir(parents=True, exist_ok=True)
    tmp = destination.with_suffix(".json.tmp")
    tmp.write_text(json.dumps({"steam_library_paths": [str(p) for p in libraries]}, indent=2) + "\n", encoding="utf-8")
    tmp.replace(destination)
    return selected


def _steam_roots() -> list[Path]:
    home = Path.home()
    return _unique_paths([
        str(home / ".local/share/Steam"),
        str(home / ".steam/steam"),
        str(home / ".steam/root"),
        str(home / ".var/app/com.valvesoftware.Steam/.local/share/Steam"),
    ])


def _libraries_from_vdf(vdf: Path) -> list[Path]:
    # Steam libraryfolders.vdf: read-only extraction of quoted "path" strings.
    # Do not interpret arbitrary VDF content as commands.
    try:
        text = vdf.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    items = []
    for match in re.finditer(r'^\s*"path"\s+"((?:\\.|[^"\\])*)"', text, re.M):
        raw = match.group(1).replace(chr(92) * 2, chr(92))
        items.append(raw)
    return _unique_paths(items)


def discover_steam_libraries() -> list[Path]:
    found = []
    for root in _steam_roots():
        found.append(root)
        found.extend(_libraries_from_vdf(root / "steamapps/libraryfolders.vdf"))
        found.extend(_libraries_from_vdf(root / "config/libraryfolders.vdf"))
    found.extend(load_user_libraries())
    return [p for p in _unique_paths(str(x) for x in found) if (p / "steamapps").is_dir()]


def installed_appids(library: Path) -> list[str]:
    steamapps = library / "steamapps"
    return sorted((m.group(1) for f in steamapps.glob("appmanifest_*.acf")
                   if (m := re.fullmatch(r"appmanifest_(\d+)\.acf", f.name))), key=int)


def proton_prefix_path(library: Path, appid: str) -> Path | None:
    if not re.fullmatch(r"\d+", str(appid)):
        raise ValueError("AppID must contain digits only")
    path = library / "steamapps" / "compatdata" / str(appid) / "pfx"
    return path if path.is_dir() else None
