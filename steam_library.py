"""RyuSCOPE GS Steam Library Manager, phase-one read-only Steam discovery.

Only the user's own RyuSCOPE configuration file is written. Steam manifests,
config files, libraries, Proton prefixes and installed games are never modified.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


class SteamLibraryError(RuntimeError):
    """Invalid library, corrupt configuration, or unable to start Steam."""


@dataclass(frozen=True)
class SteamGame:
    app_id: int
    name: str
    library: Path
    directory: Path
    state_flags: int
    files_present: bool

    @property
    def is_steam_tool(self) -> bool:
        # Manifests do not provide a reliable 'game versus tool' field.
        # This is a display-only heuristic; the Show tools toggle reveals them.
        name = self.name.casefold()
        return name.startswith(('proton ', 'steam linux runtime', 'steam runtime',
                                'steamworks common redistributables', 'steam input configs'))

    @property
    def status(self) -> str:
        if not self.files_present:
            return 'Files missing'
        if not (self.state_flags & 4):
            return 'Updating / incomplete'
        return 'Installed'


def _tokens(text: str) -> list[str]:
    """Read the subset of Steam's KeyValues1/VDF syntax used by library manifests."""
    tokens: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        if text[i].isspace():
            i += 1
            continue
        if text.startswith('//', i):
            nl = text.find('\n', i)
            i = n if nl == -1 else nl + 1
            continue
        if text[i] in '{}':
            tokens.append(text[i])
            i += 1
            continue
        if text[i] == '"':
            i += 1
            buf: list[str] = []
            while i < n:
                char = text[i]
                if char == '"':
                    i += 1
                    break
                if char == '\\' and i + 1 < n and text[i + 1] in ('\\', '"'):
                    buf.append(text[i + 1])
                    i += 2
                    continue
                buf.append(char)
                i += 1
            else:
                raise SteamLibraryError('Unterminated quoted VDF string.')
            tokens.append(''.join(buf))
            continue
        end = i
        while end < n and not text[end].isspace() and text[end] not in '{}':
            if text.startswith('//', end):
                break
            end += 1
        if end == i:
            raise SteamLibraryError('Invalid VDF syntax.')
        tokens.append(text[i:end])
        i = end
    return tokens


def parse_vdf(text: str) -> dict:
    """Parse nested KeyValues pairs; do not evaluate directives or execute content."""
    tokens = _tokens(text)
    pos = 0

    def parse_block(depth: int, wrapped: bool) -> dict:
        nonlocal pos
        if depth > 32:
            raise SteamLibraryError('VDF nested too deeply.')
        obj: dict = {}
        while pos < len(tokens):
            key = tokens[pos]
            pos += 1
            if key == '}':
                if not wrapped:
                    raise SteamLibraryError('Unexpected closing VDF brace.')
                return obj
            if key == '{':
                raise SteamLibraryError('Unexpected opening VDF brace.')
            if pos >= len(tokens):
                raise SteamLibraryError('VDF key has no value.')
            value = tokens[pos]
            pos += 1
            if value == '{':
                obj[key] = parse_block(depth + 1, True)
            elif value == '}':
                raise SteamLibraryError('VDF value missing before closing brace.')
            else:
                obj[key] = value
        if wrapped:
            raise SteamLibraryError('Unclosed VDF brace.')
        return obj

    result = parse_block(0, False)
    if pos != len(tokens):
        raise SteamLibraryError('Unexpected VDF content after the root block.')
    return result


def _case_get(mapping: dict, key: str, default=None):
    return next((v for k, v in mapping.items() if k.lower() == key.lower()), default)


def _read_vdf(path: Path) -> dict:
    if path.stat().st_size > 8_000_000:
        raise SteamLibraryError(f'Manifest unexpectedly large: {path.name}')
    return parse_vdf(path.read_text(encoding='utf-8-sig', errors='replace'))


def library_root(path: str | Path) -> Path:
    """Accept either SteamLibrary or SteamLibrary/steamapps, without touching files."""
    raw = Path(path).expanduser().resolve()
    if raw.name.lower() == 'steamapps':
        raw = raw.parent
    if not (raw / 'steamapps').is_dir():
        raise SteamLibraryError(f'Not a Steam library (steamapps not found): {raw}')
    return raw


def _steam_roots(home: Path | None = None) -> list[Path]:
    home = Path.home() if home is None else Path(home)
    return [
        home / '.local/share/Steam',
        home / '.steam/root',
        home / '.steam/steam',
        home / '.steam/debian-installation',
        home / '.var/app/com.valvesoftware.Steam/.local/share/Steam',
    ]


def _linked_from_index(index: Path) -> list[Path]:
    if not index.is_file():
        return []
    parsed = _read_vdf(index)
    tree = _case_get(parsed, 'libraryfolders', {})
    result: list[Path] = []
    if not isinstance(tree, dict):
        return result
    for key, entry in tree.items():
        if not str(key).isdigit():
            continue
        raw = _case_get(entry, 'path') if isinstance(entry, dict) else entry
        if isinstance(raw, str) and raw.strip():
            result.append(Path(raw))
    return result


def config_path() -> Path:
    root = os.environ.get('XDG_CONFIG_HOME')
    base = Path(root).expanduser() if root else Path.home() / '.config'
    return base / 'RyuSCOPE-GS' / 'steam_libraries.json'


def load_manual_libraries(path: Path | None = None) -> list[str]:
    target = path or config_path()
    if not target.is_file():
        return []
    try:
        obj = json.loads(target.read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise SteamLibraryError(f'Cannot read RyuSCOPE library list: {exc}') from exc
    if not isinstance(obj, dict) or obj.get('version') != 1 or not isinstance(obj.get('libraries'), list):
        raise SteamLibraryError('Invalid RyuSCOPE library list format.')
    values = obj['libraries']
    if not all(isinstance(value, str) and value.strip() for value in values):
        raise SteamLibraryError('Invalid library path in RyuSCOPE configuration.')
    return values


def save_manual_libraries(paths: list[str], path: Path | None = None) -> None:
    """Write ONLY our own config atomically; never write in a Steam library."""
    target = path or config_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps({'version': 1, 'libraries': paths}, indent=2) + '\n'
    tmp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=target.parent,
                                         prefix='.libraries-', suffix='.tmp', delete=False) as tmp:
            tmp_name = tmp.name
            tmp.write(content)
        os.replace(tmp_name, target)
    finally:
        if tmp_name and os.path.exists(tmp_name):
            os.unlink(tmp_name)


def find_libraries(manual: list[str] | None = None, home: Path | None = None) -> tuple[list[Path], list[str]]:
    """Find standard, Steam-indexed and user-linked libraries, retaining diagnostics."""
    candidates: list[Path] = []
    warnings: list[str] = []
    # Both locations appear on actual Steam installs.  Read both and
    # deduplicate roots by resolved path, including symlink aliases.
    for root in _steam_roots(home):
        if (root / 'steamapps').is_dir():
            candidates.append(root)
            for index in (root / 'config/libraryfolders.vdf',
                          root / 'steamapps/libraryfolders.vdf'):
                try:
                    candidates.extend(_linked_from_index(index))
                except (SteamLibraryError, OSError) as exc:
                    warnings.append(f'Cannot read {index}: {exc}')
    candidates.extend(Path(p) for p in (manual or []))
    seen: set[Path] = set()
    libraries: list[Path] = []
    for candidate in candidates:
        try:
            root = library_root(candidate)
            if root not in seen:
                libraries.append(root)
                seen.add(root)
        except (SteamLibraryError, OSError) as exc:
            warnings.append(str(exc))
    return libraries, warnings


def scan_libraries(libraries: list[Path]) -> tuple[list[SteamGame], list[str]]:
    """Read Steam app manifests only, one game per unique App ID."""
    games: dict[int, SteamGame] = {}
    warnings: list[str] = []
    for root in libraries:
        apps = root / 'steamapps'
        try:
            manifests = sorted(apps.glob('appmanifest_*.acf'))
        except OSError as exc:
            warnings.append(f'Cannot scan {apps}: {exc}')
            continue
        for manifest in manifests:
            match = re.fullmatch(r'appmanifest_(\d+)\.acf', manifest.name)
            if not match:
                continue
            try:
                data = _case_get(_read_vdf(manifest), 'AppState')
                if not isinstance(data, dict):
                    raise SteamLibraryError('Missing AppState block')
                app_id = int(_case_get(data, 'appid', match.group(1)))
                if app_id != int(match.group(1)) or app_id <= 0:
                    raise SteamLibraryError('Manifest App ID does not match filename')
                game_name = str(_case_get(data, 'name', f'App {app_id}')).strip()
                installed = str(_case_get(data, 'installdir', '')).strip()
                if not installed or Path(installed).name != installed or installed in ('.', '..') or '\\' in installed:
                    raise SteamLibraryError('Invalid installation directory')
                directory = (apps / 'common' / installed)
                state_flags = int(_case_get(data, 'StateFlags', '0'))
                game = SteamGame(app_id, game_name or f'App {app_id}', root,
                                 directory, state_flags, directory.is_dir())
                if app_id not in games or (game.files_present and not games[app_id].files_present):
                    games[app_id] = game
            except (OSError, ValueError, SteamLibraryError) as exc:
                warnings.append(f'{manifest.name}: {exc}')
    return sorted(games.values(), key=lambda g: (g.name.casefold(), g.app_id)), warnings


def steam_launch_argv(app_id: int) -> list[str]:
    if isinstance(app_id, bool) or not isinstance(app_id, int) or not 1 <= app_id <= 9_999_999_999:
        raise SteamLibraryError('Invalid Steam App ID.')
    if shutil.which('steam') is None:
        raise SteamLibraryError('Steam command not found. Start/check your native Steam installation.')
    return ['steam', '-applaunch', str(app_id)]


def launch_steam_game(app_id: int) -> subprocess.Popen:
    """Ask Steam to launch its own game, preserving its native/Proton selection."""
    argv = steam_launch_argv(app_id)
    try:
        return subprocess.Popen(argv, shell=False, start_new_session=True)
    except OSError as exc:
        raise SteamLibraryError(f'Could not contact Steam: {exc}') from exc
