"""RyuFG's AFMF provider. Only the game command receives activation settings."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import sys
import tempfile
from pathlib import Path

LAYER = 'VK_LAYER_AFMF'
GATE = 'RYUSCOPE_RYUFG'
LIBRARY = 'libafmf-linux.so'
MANIFEST = 'ryuscope-ryufg.json'
CONFLICT = re.compile(r'lsfg[-_ ]?vk|ls_frame_generation|optiscaler|dlssg.to.fsr3|smooth.motion', re.I)
OVERRIDE = re.compile(r'\b(?:AFMF_ENABLE|DISABLE_AFMF|AFMF_GAMESCOPE|RYUSCOPE_RYUFG|'
                      r'VK_IMPLICIT_LAYER_PATH|VK_ADD_IMPLICIT_LAYER_PATH)\s*=')


class RyuFGError(RuntimeError):
    pass


def payload() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).resolve().parent / 'plugins' / 'ryufg'
    return Path(__file__).resolve().parents[1] / 'build' / 'ryufg'


def data_home() -> Path:
    value = Path(os.environ.get('XDG_DATA_HOME') or Path.home() / '.local/share')
    return value if value.is_absolute() else Path.home() / '.local/share'


def registered_manifest() -> Path:
    return data_home() / 'vulkan' / 'implicit_layer.d' / MANIFEST


def read_payload() -> tuple[Path, dict]:
    root = payload()
    if platform.system() != 'Linux' or platform.machine() != 'x86_64':
        raise RyuFGError('RyuFG requires 64-bit x86 Linux.')
    if ':' in str(root) or '\n' in str(root):
        raise RyuFGError('Move RyuFG to a directory without colons or line breaks.')
    try:
        document = json.loads((root / MANIFEST).read_text())
        layer = document['layer']
        if (layer['name'] != LAYER or layer['library_path'] != './' + LIBRARY
                or layer['enable_environment'] != {GATE: '1'}
                or layer['disable_environment'] != {'DISABLE_AFMF': '1'}):
            raise ValueError('unexpected manifest')
        with (root / LIBRARY).open('rb') as binary:
            header = binary.read(20)
        if header[:6] != b'\x7fELF\x02\x01' or header[18:20] != b'\x3e\x00':
            raise ValueError('expected an x86-64 ELF layer')
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise RyuFGError(f'RyuFG package unavailable at {root}. Build or reinstall the plugin ({exc}).') from exc
    return root, document


def conflict_check(existing: str = '', game_dir: Path | None = None) -> None:
    if CONFLICT.search(existing) or OVERRIDE.search(existing) or LAYER in existing:
        raise RyuFGError('Remove the conflicting frame generation or Vulkan layer settings from the game launch options.')
    if os.environ.get('DISABLE_AFMF') == '1':
        raise RyuFGError('DISABLE_AFMF=1 is set in the launcher environment.')
    if os.environ.get('VK_IMPLICIT_LAYER_PATH'):
        raise RyuFGError('VK_IMPLICIT_LAYER_PATH overrides normal Vulkan layer discovery.')
    for key in ('VK_INSTANCE_LAYERS', 'VK_LOADER_LAYERS_ENABLE', 'VK_LOADER_LAYERS_ALLOW',
                'LD_PRELOAD', 'WINEDLLOVERRIDES'):
        value = os.environ.get(key, '')
        if CONFLICT.search(value) or LAYER in value:
            raise RyuFGError(f'Conflicting Vulkan layer or frame generator in {key}.')
    if game_dir:
        try:
            for entry in game_dir.iterdir():
                if CONFLICT.search(entry.name):
                    raise RyuFGError(f'Possible frame generation injector in the game directory: {entry.name}.')
        except OSError as exc:
            raise RyuFGError(f'Cannot check game directory for frame generation injectors: {exc}') from exc
    env = os.environ
    config_home = env.get('XDG_CONFIG_HOME') or str(Path.home() / '.config')
    directories = [config_home, *env.get('XDG_CONFIG_DIRS', '/etc/xdg').split(':'),
                   '/etc', '/usr/local/etc', str(data_home()),
                   *env.get('XDG_DATA_DIRS', '/usr/local/share:/usr/share').split(':')]
    implicit = [Path(directory) / 'vulkan' / 'implicit_layer.d'
                for directory in directories if directory]
    implicit.extend(Path(path) for path in env.get('VK_ADD_IMPLICIT_LAYER_PATH', '').split(':') if path)
    explicit = [Path(path) for key in ('VK_LAYER_PATH', 'VK_ADD_LAYER_PATH')
                for path in env.get(key, '').split(':') if path]
    for directory in dict.fromkeys(implicit + explicit):
        for manifest in directory.glob('*.json'):
            try:
                document = json.loads(manifest.read_text())
                layers = [document.get('layer'), *document.get('layers', [])]
            except (OSError, ValueError, TypeError, AttributeError):
                layers = []
            for layer in layers:
                if not isinstance(layer, dict):
                    continue
                name = layer.get('name', '')
                library = layer.get('library_path', '')
                managed = (manifest == registered_manifest()
                           and layer.get('enable_environment') == {GATE: '1'})
                if name == LAYER and not managed:
                    raise RyuFGError(f'Another AFMF manifest is installed: {manifest}.')
                if directory in implicit and CONFLICT.search(f'{name} {library}'):
                    raise RyuFGError(f'Conflicting implicit frame generation layer: {manifest}.')


def publish_file(target: Path, data: bytes) -> None:
    """Publish a complete file without replacing a different existing installation."""
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=target.parent) as temporary:
        temporary.write(data)
        temporary.flush()
        try:
            os.link(temporary.name, target)
        except FileExistsError:
            if target.is_symlink() or target.read_bytes() != data:
                raise RyuFGError(f'Conflicting RyuFG installation at {target}.')


def prepare_steam() -> None:
    """Stage a dormant layer where pressure-vessel discovers host implicit layers."""
    root, document = read_payload()
    conflict_check()
    try:
        binary = (root / LIBRARY).read_bytes()
        digest = hashlib.sha256(binary).hexdigest()
        target = data_home() / 'ryuscope' / 'ryufg' / digest / LIBRARY
        document['layer']['library_path'] = str(target)
        for notice in ('LICENSE-AFMF.txt', 'LICENSE-FidelityFX.txt', 'UPSTREAM.txt'):
            publish_file(target.parent / notice, (root / notice).read_bytes())
        publish_file(target, binary)
        publish_file(registered_manifest(), (json.dumps(document, indent=2) + '\n').encode())
    except OSError as exc:
        raise RyuFGError(f'Could not stage the RyuFG Steam layer: {exc}') from exc


def game_prefix(enabled: bool, *, steam: bool = False, gamescope: bool = True,
                existing: str = '', game_dir: Path | None = None) -> list[str]:
    if not enabled:
        return ['env', 'DISABLE_AFMF=1']
    root, _ = read_payload()
    conflict_check(existing, game_dir)
    settings = ['env', '-u', 'DISABLE_AFMF', f'{GATE}=1', 'AFMF_ENABLE=1']
    if gamescope:
        settings.append('AFMF_GAMESCOPE=1')
    if not steam:
        additional = os.environ.get('VK_ADD_IMPLICIT_LAYER_PATH')
        paths = str(root) + (':' + additional if additional else '')
        settings.append('VK_ADD_IMPLICIT_LAYER_PATH=' + paths)
    return settings


def status() -> str:
    try:
        root, _ = read_payload()
        conflict_check()
    except RyuFGError as exc:
        return str(exc)
    return f'RyuFG layer package ready at {root}. Frame generation requires in-game verification.'
