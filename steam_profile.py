"""RyuSCOPE GS v0.5: conservative, reversible Steam LaunchOptions editor.

Steam must be closed before writes. Edits target one app in the real
UserLocalConfigStore/Software/Valve/Steam/apps hierarchy, preserving every
other byte of localconfig.vdf. No Proton prefix or game directory is touched.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from integrations import GamescopeOptions, IntegrationError, build_gamescope_args, ryufg_prefix
from plugins import ryufg


class SteamProfileError(RuntimeError):
    pass


@dataclass
class Token:
    value: str
    start: int
    end: int
    kind: str


@dataclass
class Entry:
    key: Token
    value: Token | None = None
    child: 'Block | None' = None


@dataclass
class Block:
    opener: Token | None
    closer: Token | None
    entries: list[Entry]


def _lex(source: str) -> list[Token]:
    result = []
    i = 0
    while i < len(source):
        if source[i].isspace():
            i += 1
            continue
        if source.startswith('//', i):
            end = source.find('\n', i)
            i = len(source) if end < 0 else end + 1
            continue
        start = i
        if source[i] in '{}':
            result.append(Token(source[i], i, i + 1, 'brace'))
            i += 1
            continue
        if source[i] == '"':
            chars = []
            i += 1
            while i < len(source):
                if source[i] == '"':
                    i += 1
                    result.append(Token(''.join(chars), start, i, 'str'))
                    break
                if source[i] == '\\' and i + 1 < len(source) and source[i+1] in ('"', '\\'):
                    chars.append(source[i + 1])
                    i += 2
                else:
                    chars.append(source[i])
                    i += 1
            else:
                raise SteamProfileError('Unterminated VDF string; file not modified.')
            continue
        while i < len(source) and not source[i].isspace() and source[i] not in '{}':
            if source.startswith('//', i):
                break
            i += 1
        if i == start:
            raise SteamProfileError('Malformed VDF token; file not modified.')
        result.append(Token(source[start:i], start, i, 'str'))
    return result


def _parse(source: str) -> Block:
    tokens = _lex(source)
    pos = 0

    def block(opener: Token | None, depth: int) -> Block:
        nonlocal pos
        if depth > 60:
            raise SteamProfileError('VDF nesting too deep.')
        entries = []
        while pos < len(tokens):
            token = tokens[pos]
            pos += 1
            if token.value == '}' and token.kind == 'brace':
                if opener is None:
                    raise SteamProfileError('Unexpected VDF closing brace.')
                return Block(opener, token, entries)
            if token.kind == 'brace':
                raise SteamProfileError('Unexpected VDF opening brace.')
            if pos >= len(tokens):
                raise SteamProfileError('VDF key lacks a value.')
            next_token = tokens[pos]
            pos += 1
            if next_token.kind == 'brace' and next_token.value == '{':
                entries.append(Entry(token, child=block(next_token, depth + 1)))
            elif next_token.kind != 'brace':
                entries.append(Entry(token, value=next_token))
            else:
                raise SteamProfileError('VDF key has a missing value.')
        if opener is not None:
            raise SteamProfileError('Unclosed VDF block.')
        return Block(None, None, entries)

    root = block(None, 0)
    if pos != len(tokens):
        raise SteamProfileError('Extra data after VDF root.')
    return root


def _entry(block: Block, name: str) -> Entry | None:
    found = [e for e in block.entries if e.key.value.casefold() == name.casefold()]
    if len(found) > 1:
        raise SteamProfileError(f'Ambiguous duplicate VDF key: {name}; refusing edit.')
    return found[0] if found else None


def _child(parent: Block, name: str) -> Block | None:
    found = _entry(parent, name)
    if found is None:
        return None
    if found.child is None:
        raise SteamProfileError(f'VDF {name} should be a section, not a value.')
    return found.child


def _apps_root(root: Block) -> Block:
    current = root
    for key in ('UserLocalConfigStore', 'Software', 'Valve', 'Steam', 'apps'):
        current = _child(current, key)
        if current is None:
            raise SteamProfileError(f'Steam configuration does not have expected {key} section.')
    return current


def _app_block(root: Block, app_id: int) -> Block | None:
    return _child(_apps_root(root), str(_check_app_id(app_id)))


def _check_app_id(app_id: int) -> int:
    if type(app_id) is not int or not 1 <= app_id <= 9_999_999_999:
        raise SteamProfileError('Invalid Steam App ID.')
    return app_id


def _escape(text: str) -> str:
    return '"' + text.replace('\\', '\\\\').replace('"', '\\"') + '"'


def _line_indent(source: str, offset: int) -> str:
    start = source.rfind('\n', 0, offset) + 1
    prefix = source[start:offset]
    return prefix if not prefix.strip() else ''


def _insert_before_close(source: str, block: Block, line: str) -> str:
    close = block.closer
    if close is None:
        raise SteamProfileError('Cannot insert outside a VDF section.')
    indent = _line_indent(source, close.start)
    if indent or source[close.start - 1:close.start] == '\n':
        # Place at beginning of the closing-brace line, preserving the old line.
        start = source.rfind('\n', 0, close.start) + 1
        return source[:start] + line + '\n' + source[start:]
    # Compact one-line VDF section.
    return source[:close.start] + '\n' + line + '\n' + source[close.start:]


def _indent_for_child(source: str, parent: Block) -> str:
    if parent.entries:
        existing = _line_indent(source, parent.entries[0].key.start)
        if existing:
            return existing
    close_indent = _line_indent(source, parent.closer.start) if parent.closer else ''
    return close_indent + ('\t' if '\t' in close_indent else '    ')


def launch_options_from_text(source: str, app_id: int) -> str | None:
    game = _app_block(_parse(source), app_id)
    if game is None:
        return None
    option = _entry(game, 'LaunchOptions')
    if option is None:
        return None
    if option.value is None:
        raise SteamProfileError('LaunchOptions is not a string.')
    return option.value.value


def edit_launch_options(source: str, app_id: int, new_value: str | None) -> str:
    """Surgically replace/insert/remove only the selected app's LaunchOptions."""
    if new_value is not None and ('\x00' in new_value or '\r' in new_value or '\n' in new_value):
        raise SteamProfileError('Invalid line break or NUL in launch options.')
    root = _parse(source)
    apps = _apps_root(root)
    game = _child(apps, str(_check_app_id(app_id)))
    if game is None:
        if new_value is None:
            return source
        child_indent = _indent_for_child(source, apps)
        property_indent = child_indent + ('\t' if '\t' in child_indent else '    ')
        addition = (f'{child_indent}"{app_id}"\n{child_indent}{{\n'
                    f'{property_indent}"LaunchOptions"\t\t{_escape(new_value)}\n'
                    f'{child_indent}}}')
        return _insert_before_close(source, apps, addition)
    option = _entry(game, 'LaunchOptions')
    if option is not None:
        if option.value is None:
            raise SteamProfileError('LaunchOptions has unexpected structure.')
        if new_value is None:
            # Remove only the property line (if standalone), not the whole app block.
            line_start = source.rfind('\n', 0, option.key.start) + 1
            line_end = source.find('\n', option.value.end)
            if (not source[line_start:option.key.start].strip() and
                    not source[option.value.end:line_end if line_end >= 0 else len(source)].strip()):
                return source[:line_start] + source[line_end + 1 if line_end >= 0 else len(source):]
            return source[:option.key.start] + source[option.value.end:]
        return source[:option.value.start] + _escape(new_value) + source[option.value.end:]
    if new_value is None:
        return source
    child_indent = _indent_for_child(source, game)
    return _insert_before_close(source, game, f'{child_indent}"LaunchOptions"\t\t{_escape(new_value)}')


def _file_text(path: Path) -> str:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 20_000_000:
        raise SteamProfileError(f'Steam localconfig not found or unexpectedly large: {path}')
    return path.read_text(encoding='utf-8', errors='surrogateescape')


def discover_localconfigs(home: Path | None = None) -> list[Path]:
    home = Path.home() if home is None else Path(home)
    roots = [home / '.local/share/Steam', home / '.steam/root', home / '.steam/steam',
             home / '.var/app/com.valvesoftware.Steam/.local/share/Steam']
    found = set()
    for root in roots:
        for path in root.glob('userdata/*/config/localconfig.vdf'):
            if path.is_file() and path.parent.parent.name.isdigit():
                found.add(path.resolve())
    return sorted(found)


def steam_is_running() -> bool:
    """Check current user's native Steam process, not Wine's steam.exe or reaper."""
    proc = Path('/proc')
    if not proc.is_dir():
        raise SteamProfileError('Cannot verify whether Steam is running (/proc unavailable).')
    for item in proc.iterdir():
        if not item.name.isdigit():
            continue
        try:
            if item.stat().st_uid != os.getuid():
                continue
            comm = (item / 'comm').read_text(encoding='utf-8').strip()
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
        if comm in ('steam', 'steam.sh'):
            return True
    return False


def request_steam_quit() -> None:
    binary = shutil.which('steam')
    if not binary:
        raise SteamProfileError('Steam executable not found.')
    try:
        subprocess.Popen([binary, '-shutdown'], start_new_session=True, shell=False)
    except OSError as exc:
        raise SteamProfileError(f'Could not request Steam quit: {exc}') from exc


def _settings_dir() -> Path:
    xdg = os.environ.get('XDG_CONFIG_HOME')
    return (Path(xdg).expanduser() if xdg else Path.home() / '.config') / 'RyuSCOPE-GS'


def _private_dir() -> Path:
    target = _settings_dir() / 'steam-profile-backups'
    target.mkdir(mode=0o700, parents=True, exist_ok=True)
    target.chmod(0o700)
    return target


def _state_file(custom: Path | None = None) -> Path:
    return custom if custom is not None else _settings_dir() / 'steam_profile_state.json'


def _record_key(config: Path, app_id: int) -> str:
    return str(config.resolve()) + '#' + str(_check_app_id(app_id))


def _load_state(path: Path) -> dict:
    if not path.exists():
        return {'version': 1, 'entries': {}}
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise SteamProfileError(f'Cannot read RyuSCOPE restore records: {exc}') from exc
    if not isinstance(data, dict) or data.get('version') != 1 or not isinstance(data.get('entries'), dict):
        raise SteamProfileError('Invalid restore-record file. Refusing to modify Steam.')
    for record in data['entries'].values():
        if (not isinstance(record, dict) or
                not isinstance(record.get('applied'), str) or
                (record.get('original') is not None and not isinstance(record['original'], str))):
            raise SteamProfileError('Malformed RyuSCOPE restore record. Refusing to modify Steam.')
    return data


def _atomic_bytes(target: Path, data: bytes, mode: int = 0o600) -> None:
    tmp_name = None
    try:
        fd, tmp_name = tempfile.mkstemp(prefix='.ryuscope-', dir=target.parent)
        with os.fdopen(fd, 'wb') as f:
            os.fchmod(f.fileno(), mode)
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_name, target)
        tmp_name = None
    finally:
        if tmp_name and os.path.exists(tmp_name):
            os.unlink(tmp_name)


def _save_state(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_bytes(path, (json.dumps(data, indent=2) + '\n').encode('utf-8'), 0o600)


def _backup(config: Path, state_path: Path) -> Path:
    directory = _private_dir() if state_path == _state_file() else (state_path.parent / "steam-profile-backups")
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    directory.chmod(0o700)
    backup = directory / f'{config.parent.parent.name}-{int(time.time())}-{uuid.uuid4().hex[:8]}.vdf'
    original = config.read_bytes()
    with backup.open('xb') as handle:
        os.fchmod(handle.fileno(), 0o600)
        handle.write(original)
        handle.flush()
        os.fsync(handle.fileno())
    return backup


def _write_with_record(config: Path, old_text: str, new_text: str, state_path: Path,
                       state: dict, running: Callable[[], bool]) -> Path:
    if running():
        raise SteamProfileError('Steam started again. Quit Steam before applying changes.')
    if _file_text(config) != old_text:
        raise SteamProfileError('Steam config changed during preparation. Retry after closing Steam.')
    backup = _backup(config, state_path)
    mode = config.stat().st_mode & 0o777
    try:
        _atomic_bytes(config, new_text.encode('utf-8', errors='surrogateescape'), mode)
        if _file_text(config) != new_text:
            raise SteamProfileError('Steam configuration failed post-write verification.')
        _save_state(state_path, state)
    except Exception as exc:
        # If RyuSCOPE itself failed after the Steam edit, try to revert only if
        # the file still contains precisely our version. Never erase an external edit.
        try:
            if _file_text(config) == new_text:
                _atomic_bytes(config, old_text.encode('utf-8', errors='surrogateescape'), mode)
        except Exception as rollback_exc:
            raise SteamProfileError(f'Could not finish write or auto-rollback. Backup: {backup}: {rollback_exc}') from exc
        raise SteamProfileError(f'Configuration write aborted. Backup: {backup}: {exc}') from exc
    return backup


def _migrate_legacy_mangohud(existing: str | None) -> str | None:
    """Only remove a simple *leading* MangoHud activation prefix.

    Preserve all unrelated options, and refuse complex/ambiguous MangoHud
    invocation rather than risk deleting user launch behavior.
    The original string is always kept in RyuSCOPE's restore record.
    """
    if not existing:
        return existing
    remainder = existing.strip()
    prefixes = (r'^MANGOHUD=1\s+', r'^mangohud\s+')
    for prefix in prefixes:
        result = re.sub(prefix, '', remainder, count=1, flags=re.IGNORECASE)
        if result != remainder:
            if re.search(r'(?<![\w-])(?:MANGOHUD=1|mangohud)(?![\w-])', result, re.I):
                raise SteamProfileError('Complex MangoHud launch options require manual review; no changes made.')
            return result
    if re.search(r'(?<![\w-])(?:MANGOHUD=1|mangohud)(?![\w-])', remainder, re.I):
        raise SteamProfileError('Complex MangoHud launch options require manual review; no changes made.')
    return existing


def compose_launch_options(existing: str | None, args: list[str], mango_config: str = '',
                           *, child: list[str] | None = None) -> str:
    if not args or 'gamescope' not in args:
        raise SteamProfileError('Generated command has no Gamescope executable.')
    # Steam substitutes %command%. Prefix/suffix settings are retained verbatim.
    settings = [f'MANGOHUD_CONFIG={mango_config}'] if mango_config else []
    if child:
        # Existing wrappers may require an executable immediately before %command%.
        wrapper = shlex.join(['env', *settings, 'DISABLE_AFMF=1', *args, '--', *child]) + ' '
    else:
        prefix = 'MANGOHUD_CONFIG=' + shlex.quote(mango_config) + ' ' if mango_config else ''
        wrapper = prefix + shlex.join(args) + ' -- '
    if existing is None or not existing.strip():
        return wrapper + '%command%'
    if existing.count('%command%') != 1:
        raise SteamProfileError('Existing launch options must have exactly one %command% placeholder.')
    if re.search(r'(?<![\w-])gamescope(?![\w-])', existing, re.IGNORECASE):
        raise SteamProfileError('Existing options already mention Gamescope. Refusing to double-wrap.')
    return existing.replace('%command%', wrapper + '%command%')


def profile_status(config: Path, app_id: int, *, state_path: Path | None = None) -> tuple[str, str | None]:
    """Return ('Not applied'|'Applied'|'Modified elsewhere'|'Not yet written', current)."""
    current = launch_options_from_text(_file_text(config), app_id)
    record = _load_state(_state_file(state_path))['entries'].get(_record_key(config, app_id))
    if not record:
        return 'Not applied', current
    if current == record['applied']:
        return 'Applied', current
    if current == record['original']:
        return 'Not yet written / restored externally', current
    return 'Modified elsewhere', current


def apply_profile(config: Path, app_id: int, o: GamescopeOptions, flags: set[str] | None,
                  *, mango_config: str = '', state_path: Path | None = None,
                  game_dir: Path | None = None,
                  running: Callable[[], bool] = steam_is_running) -> tuple[str, Path | None]:
    if running():
        raise SteamProfileError('Steam is running. Quit Steam completely before applying a Gamescope profile.')
    if flags is None:
        raise SteamProfileError('Gamescope flags are not validated on this PC.')
    config = Path(config)
    path = _state_file(state_path)
    state = _load_state(path)
    key = _record_key(config, app_id)
    old_text = _file_text(config)
    current = launch_options_from_text(old_text, app_id)
    record = state['entries'].get(key)
    if record:
        if current != record['applied']:
            raise SteamProfileError('Launch options changed since RyuSCOPE last applied them. No overwrite; restore manually or investigate.')
        original = record['original']
    else:
        original = current
    # The *original* is preserved for Restore Original. When --mangoapp is
    # chosen, remove only an explicitly recognized legacy MangoHud prefix.
    # Never run two overlay injection methods simultaneously.
    base = _migrate_legacy_mangohud(original) if o.mangoapp else original
    args = build_gamescope_args(o, flags)
    # Re-applying our settings must wrap the ORIGINAL, never the previously wrapped value.
    next_options = _compose_profile(base, args, o, mango_config, game_dir)
    if o.ryufg:
        try:
            ryufg.prepare_steam()
        except ryufg.RyuFGError as exc:
            raise SteamProfileError(str(exc)) from exc
    if next_options == current:
        return next_options, None
    new_text = edit_launch_options(old_text, app_id, next_options)
    state['entries'][key] = {'original': original, 'applied': next_options,
                             'last_updated': int(time.time()), 'app_id': app_id,
                             'config': str(config.resolve())}
    backup = _write_with_record(config, old_text, new_text, path, state, running)
    return next_options, backup


def restore_profile(config: Path, app_id: int, *, state_path: Path | None = None,
                    running: Callable[[], bool] = steam_is_running) -> Path | None:
    if running():
        raise SteamProfileError('Steam is running. Quit Steam completely before restoring original launch options.')
    config = Path(config)
    path = _state_file(state_path)
    state = _load_state(path)
    key = _record_key(config, app_id)
    record = state['entries'].get(key)
    if not record:
        raise SteamProfileError('No RyuSCOPE restore record exists for this game/account.')
    old_text = _file_text(config)
    current = launch_options_from_text(old_text, app_id)
    if current != record['applied']:
        raise SteamProfileError('Launch options changed outside RyuSCOPE; refusing to overwrite those changes.')
    new_text = edit_launch_options(old_text, app_id, record['original'])
    del state['entries'][key]
    return _write_with_record(config, old_text, new_text, path, state, running)


def preview_profile(config: Path, app_id: int, o: GamescopeOptions, flags: set[str] | None,
                    *, mango_config: str = '', state_path: Path | None = None,
                      game_dir: Path | None = None) -> tuple[str | None, str, str]:
    """Read-only preview: current, proposed, status. Never writes Steam files."""
    if flags is None:
        raise SteamProfileError('Gamescope options are not validated yet.')
    status, current = profile_status(config, app_id, state_path=state_path)
    data = _load_state(_state_file(state_path))
    record = data['entries'].get(_record_key(config, app_id))
    base = record['original'] if record and status == 'Applied' else current
    if o.mangoapp:
        base = _migrate_legacy_mangohud(base)
    target = _compose_profile(base, build_gamescope_args(o, flags), o, mango_config, game_dir)
    return current, target, status


def _compose_profile(existing: str | None, args: list[str], options: GamescopeOptions,
                     mango_config: str, game_dir: Path | None) -> str:
    try:
        child = ryufg_prefix(options, steam=True, existing=existing or '', game_dir=game_dir)
    except IntegrationError as exc:
        raise SteamProfileError(str(exc)) from exc
    # Put compositor settings inside any existing env/launcher wrapper.
    # An env executable also works after wrappers that require a command name.
    return compose_launch_options(existing, args, mango_config, child=child)
