"""RyuSCOPE GS: read-only Ryujinx game discovery and safe external launch.

This adapter NEVER touches Ryujinx saves, firmware, keys, caches or settings.
Game files are treated as opaque paths. No shell invocation, no ROM parsing.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from integrations import (GamescopeOptions, IntegrationError,
                          build_gamescope_args, detect_command)


class RyujinxError(RuntimeError):
    pass


GAME_SUFFIXES = frozenset({'.xci', '.nsp', '.nro', '.nca'})
SOURCES = ('Auto detect', 'Custom executable / AppImage',
           'Flatpak (Ryujinx)', 'Flatpak (Ryubing)')
FLATPAK_APPS = {
    'Flatpak (Ryujinx)': 'org.ryujinx.Ryujinx',
    'Flatpak (Ryubing)': 'io.github.ryubing.Ryujinx',
}


@dataclass(frozen=True)
class RyujinxGame:
    name: str
    path: Path
    kind: str
    library: Path


def settings_path() -> Path:
    home_config = Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home() / '.config')))
    return home_config / 'RyuSCOPE-GS' / 'ryujinx.json'


def load_settings(path: Path | None = None) -> dict:
    path = path or settings_path()
    defaults = {
        'source': 'Auto detect', 'executable': '', 'game_dirs': [],
        'gamescope': True, 'fullscreen': False,
    }
    try:
        obj = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError, UnicodeError):
        return defaults
    if not isinstance(obj, dict):
        return defaults
    data = defaults.copy()
    if obj.get('source') in SOURCES:
        data['source'] = obj['source']
    if isinstance(obj.get('executable'), str):
        data['executable'] = obj['executable']
    if isinstance(obj.get('game_dirs'), list):
        data['game_dirs'] = [s for s in obj['game_dirs'] if isinstance(s, str)][:100]
    for name in ('gamescope', 'fullscreen'):
        if type(obj.get(name)) is bool:
            data[name] = obj[name]
    return data


def save_settings(data: dict, path: Path | None = None) -> None:
    path = path or settings_path()
    safe = {
        'source': data['source'] if data.get('source') in SOURCES else SOURCES[0],
        'executable': str(data.get('executable', '')),
        'game_dirs': [str(x) for x in data.get('game_dirs', [])][:100],
        'gamescope': bool(data.get('gamescope', True)),
        'fullscreen': bool(data.get('fullscreen', False)),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    import tempfile
    temp_name = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8',
                                         dir=path.parent, prefix='.ryujinx-',
                                         suffix='.tmp', delete=False) as f:
            temp_name = f.name
            json.dump(safe, f, indent=2)
            f.write('\n')
        os.chmod(temp_name, 0o600)
        os.replace(temp_name, path)
    finally:
        if temp_name and os.path.exists(temp_name):
            os.unlink(temp_name)


def read_ryujinx_game_dirs(config_paths: Iterable[Path] | None = None) -> list[str]:
    """Optional import of emulator's *folder list* only, never modifying Config.json."""
    if config_paths is None:
        base = Path.home()
        config_paths = [
            base / '.config/Ryujinx/Config.json',
            base / '.var/app/org.ryujinx.Ryujinx/config/Ryujinx/Config.json',
            base / '.var/app/io.github.ryubing.Ryujinx/config/Ryujinx/Config.json',
        ]
    found: list[str] = []
    for config in config_paths:
        try:
            obj = json.loads(Path(config).read_text(encoding='utf-8'))
        except (OSError, ValueError, UnicodeError):
            continue
        if not isinstance(obj, dict):
            continue
        for folder in obj.get('game_dirs', []):
            if isinstance(folder, str) and folder and folder not in found:
                found.append(folder)
    return found


def scan_games(folders: Iterable[str | Path], max_depth: int = 3,
               max_files: int = 10000) -> tuple[list[RyujinxGame], list[str]]:
    """Shallow read-only scan; does not parse or execute any game file.

    max_depth is relative to the selected library directory; symlink directories
    are not followed. Directories that are offline are reported, not modified.
    """
    result: list[RyujinxGame] = []
    warnings: list[str] = []
    seen: set[Path] = set()
    remaining = max_files
    for raw_folder in folders:
        root = Path(raw_folder).expanduser().resolve()
        if not root.is_dir():
            warnings.append(f'Unavailable folder: {root}')
            continue
        try:
            for parent, dirs, names in os.walk(root, followlinks=False):
                relative_depth = len(Path(parent).relative_to(root).parts)
                dirs[:] = [] if relative_depth >= max_depth else [
                    d for d in dirs if not d.startswith('.') and not (Path(parent) / d).is_symlink()
                ]
                for filename in names:
                    remaining -= 1
                    if remaining < 0:
                        warnings.append(f'Scan limit of {max_files} files reached; narrow your game folders.')
                        return sorted(result, key=lambda g: g.name.casefold()), warnings
                    file_path = Path(parent) / filename
                    if file_path.suffix.lower() not in GAME_SUFFIXES or file_path.is_symlink():
                        continue
                    if not file_path.is_file():
                        continue
                    canonical = file_path.resolve()
                    if canonical in seen:
                        continue
                    seen.add(canonical)
                    result.append(RyujinxGame(
                        file_path.stem, canonical, file_path.suffix.upper().lstrip('.'), root))
        except OSError as exc:
            warnings.append(f'Cannot read {root}: {exc}')
    return sorted(result, key=lambda g: g.name.casefold()), warnings


def resolve_runner(source: str, executable: str = '') -> list[str]:
    """Return argv prefix for installed emulator; never invoke via a shell."""
    if source not in SOURCES:
        raise RyujinxError(f'Unknown Ryujinx install type: {source}')
    if source in FLATPAK_APPS:
        flatpak = shutil.which('flatpak')
        if not flatpak:
            raise RyujinxError('Flatpak executable is not installed.')
        app = FLATPAK_APPS[source]
        try:
            check = subprocess.run([flatpak, 'info', app], capture_output=True,
                                   timeout=4, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise RyujinxError(f'Cannot inspect Flatpak installation: {exc}') from exc
        if check.returncode != 0:
            raise RyujinxError(f'Flatpak app is not installed: {app}')
        return [flatpak, 'run', app]
    if source == 'Custom executable / AppImage':
        given = executable.strip()
        if not given:
            raise RyujinxError('Select your Ryujinx executable or AppImage first.')
        target = Path(given).expanduser()
        if target.is_file():
            if not os.access(target, os.X_OK):
                raise RyujinxError(f'Not executable: {target}')
            return [str(target.resolve())]
        found = shutil.which(given) if '/' not in given else None
        if found:
            return [found]
        raise RyujinxError(f'Ryujinx executable not found: {given}')
    for command in ('Ryujinx', 'ryujinx', 'Ryujinx.sh', 'ryujinx-gtk', 'ryubing'):
        found = shutil.which(command)
        if found:
            return [found]
    raise RyujinxError('Ryujinx not found on PATH. Choose Custom executable / AppImage, or a Flatpak option.')


def build_ryujinx_command(source: str, executable: str,
                          game: str | Path | None, fullscreen: bool,
                          use_gamescope: bool, options: GamescopeOptions,
                          flags: set[str] | None = None) -> list[str]:
    runner = resolve_runner(source, executable)
    if game:
        game_path = Path(game).expanduser().resolve()
        if not game_path.is_file() or game_path.suffix.lower() not in GAME_SUFFIXES:
            raise RyujinxError('Selected game file is missing or has an unsupported extension.')
        if fullscreen:
            runner.append('--fullscreen')
        runner.append(str(game_path))
    if not use_gamescope:
        return runner
    try:
        return build_gamescope_args(options, flags) + ['--'] + runner
    except IntegrationError as exc:
        raise RyujinxError(str(exc)) from exc


def launch_ryujinx(source: str, executable: str,
                   game: str | Path | None, fullscreen: bool,
                   use_gamescope: bool, options: GamescopeOptions,
                   flags: set[str] | None = None,
                   mangohud_config: str = '') -> subprocess.Popen:
    command = build_ryujinx_command(source, executable, game, fullscreen,
                                     use_gamescope, options, flags)
    if use_gamescope:
        if not detect_command('gamescope'):
            raise RyujinxError('Gamescope is not installed.')
        if options.gamemode and not detect_command('gamemoderun'):
            raise RyujinxError('GameMode is enabled but gamemoderun is missing.')
        if options.mangoapp and not detect_command('mangoapp'):
            raise RyujinxError('Mangoapp overlay is enabled but mangoapp is missing.')
    env = os.environ.copy()
    if use_gamescope and options.mangoapp and mangohud_config:
        env['MANGOHUD_CONFIG'] = mangohud_config
    try:
        return subprocess.Popen(command, shell=False, env=env, start_new_session=True)
    except OSError as exc:
        raise RyujinxError(f'Could not launch Ryujinx: {exc}') from exc
