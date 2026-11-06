"""RyuSCOPE GS adapters: safe Gamescope, Steam, MangoHud and read-only LACT.

No shell invocation for launching programs. LACT adapter has a hard-coded
read-only command allowlist. This module NEVER edits Steam or LACT configs.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import socket
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from plugins import ryufg


class IntegrationError(RuntimeError):
    pass


@dataclass(frozen=True)
class GamescopeOptions:
    game_width: int = 1920
    game_height: int = 1080
    output_width: int = 1920
    output_height: int = 1080
    # -r is called nested refresh by Gamescope. It is not an independent GPU driver FPS limiter.
    refresh: int = 120
    frame_limit: int = 0  # Gamescope limiter; 0 disables it (not -r)
    scaler: str = 'Auto'   # Gamescope -S; separate from filter -F
    mode: str = 'Fullscreen'
    scaling: str = 'Auto / Default'
    sharpness: int = 10
    hdr: bool = False
    adaptive_sync: bool = False
    mangoapp: bool = False
    gamemode: bool = False
    ryufg: bool = False


# Only launch flags corresponding to supported, validated UI controls.
REQUIRED = {'-w', '-h', '-W', '-H', '-r'}
OPTIONAL = {'-f', '-b', '-F', '-S', '--sharpness', '--fsr-sharpness',
            '--hdr-enabled', '--adaptive-sync', '--mangoapp', '--framerate-limit'}


def detect_command(command: str) -> bool:
    return shutil.which(command) is not None


def gamescope_help(timeout: float = 4.0) -> str:
    binary = shutil.which('gamescope')
    if not binary:
        raise IntegrationError('Gamescope not found on PATH. Install gamescope to launch games.')
    try:
        result = subprocess.run([binary, '--help'], capture_output=True, text=True,
                                timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise IntegrationError(f'Unable to inspect gamescope --help: {exc}') from exc
    output = (result.stdout or '') + '\n' + (result.stderr or '')
    if not output.strip():
        raise IntegrationError('Gamescope --help returned no text; capabilities unverified.')
    return output


def detect_flags(help_text: str) -> set[str]:
    """Recognize flag *tokens*, not fragments such as '-r' within '--borderless'."""
    candidates = REQUIRED | OPTIONAL
    return {flag for flag in candidates
            if re.search(r'(?<![\w-])' + re.escape(flag) + r'(?![\w-])', help_text)}


def validate_options(o: GamescopeOptions) -> None:
    if type(o.ryufg) is not bool:
        raise IntegrationError('RyuFG must be enabled or disabled explicitly.')
    for value in (o.game_width, o.game_height, o.output_width, o.output_height):
        if not 320 <= value <= 16384:
            raise IntegrationError('Resolution must be 320–16384 pixels per dimension.')
    if not 30 <= o.refresh <= 240:
        raise IntegrationError('Refresh target must be between 30 and 240 Hz.')
    if not 0 <= o.sharpness <= 20:
        raise IntegrationError('Sharpness must be between 0 and 20.')
    if not 0 <= o.frame_limit <= 240:
        raise IntegrationError('FPS limit must be 0 (disabled) or 1–240.')
    if o.scaler not in ('Auto', 'Integer', 'Fit', 'Fill', 'Stretch'):
        raise IntegrationError('Unsupported scaler type.')
    if o.mode not in ('Fullscreen', 'Borderless', 'Windowed'):
        raise IntegrationError('Unsupported window mode.')
    if o.scaling not in ('Auto / Default', 'FSR (Gamescope built-in)', 'NIS',
                         'SGSR (Gamescope built-in)', 'Linear', 'Nearest',
                         'Pixel', 'Integer / Nearest'):
        raise IntegrationError('Unsupported filter option.')


def build_gamescope_args(o: GamescopeOptions, flags: set[str] | None = None) -> list[str]:
    """Returns command arguments without a game or a Steam placeholder.

    If flags is provided (real help result), reject unsupported *requested*
    options. A missing mandatory flag is an explicit incompatibility.
    """
    validate_options(o)
    if flags is not None:
        missing = REQUIRED - flags
        if missing:
            raise IntegrationError('Gamescope installation lacks verified required flags: ' + ', '.join(sorted(missing)))
    result = ['gamescope', '-w', str(o.game_width), '-h', str(o.game_height),
              '-W', str(o.output_width), '-H', str(o.output_height), '-r', str(o.refresh)]

    def add(*tokens: str) -> None:
        if flags is not None and tokens[0] not in flags:
            raise IntegrationError(f'Installed Gamescope does not advertise {tokens[0]}.')
        result.extend(tokens)

    if o.frame_limit:
        add('--framerate-limit', str(o.frame_limit))
    # -S is the scaler and -F is the filter; they must remain independent.
    if o.scaler != 'Auto':
        add('-S', o.scaler.lower())
    if o.mode == 'Fullscreen':
        add('-f')
    elif o.mode == 'Borderless':
        add('-b')
    if o.scaling == 'FSR (Gamescope built-in)':
        add('-F', 'fsr')
    elif o.scaling == 'NIS':
        add('-F', 'nis')
    elif o.scaling == 'SGSR (Gamescope built-in)':
        add('-F', 'sgsr')
    elif o.scaling in ('Linear', 'Nearest', 'Pixel'):
        add('-F', o.scaling.lower())
    elif o.scaling == 'Integer / Nearest':
        # Preserve old JSON profiles, which used this combined setting.
        if o.scaler == 'Auto':
            add('-S', 'integer')
        else:
            add('-F', 'nearest')
    if o.scaling in ('FSR (Gamescope built-in)', 'NIS', 'SGSR (Gamescope built-in)'):
        sharpness_flag = '--sharpness' if flags is None or '--sharpness' in flags else '--fsr-sharpness'
        add(sharpness_flag, str(o.sharpness))
    if o.hdr:
        add('--hdr-enabled')
    if o.adaptive_sync:
        add('--adaptive-sync')
    if o.mangoapp:
        add('--mangoapp')
    if o.gamemode:
        if not detect_command('gamemoderun'):
            # For preview, optional wrapper can be shown even when not installed.
            # The actual launch path validates binaries separately.
            pass
        result.insert(0, 'gamemoderun')
    return result


def steam_launch_options(o: GamescopeOptions, flags: set[str] | None = None,
                         mangohud_config: str = '') -> str:
    prefix = build_gamescope_args(o, flags)
    # MangoHud env configuration is scoped to this game. We do not modify any global file.
    env = ('MANGOHUD_CONFIG=' + shlex.quote(mangohud_config) + ' ') if o.mangoapp and mangohud_config else ''
    child = ryufg_prefix(o, steam=True)
    return env + 'DISABLE_AFMF=1 ' + shlex.join(prefix + ['--'] + child) + ' %command%'


def ryufg_prefix(o: GamescopeOptions, **kwargs) -> list[str]:
    try:
        return ryufg.game_prefix(o.ryufg, **kwargs)
    except ryufg.RyuFGError as exc:
        raise IntegrationError(str(exc)) from exc


def direct_command(o: GamescopeOptions, executable: str, arguments: str,
                   flags: set[str] | None = None) -> list[str]:
    game = executable.strip()
    if not game:
        raise IntegrationError('Choose a game or emulator executable first.')
    binary = game if os.path.isfile(game) else shutil.which(game)
    if not binary or not os.access(binary, os.X_OK):
        raise IntegrationError(f'Executable not found or not executable: {game}')
    try:
        extra = shlex.split(arguments, posix=True)
    except ValueError as exc:
        raise IntegrationError(f'Invalid arguments: {exc}') from exc
    child = ryufg_prefix(o, existing=arguments, game_dir=Path(binary).resolve().parent)
    return build_gamescope_args(o, flags) + ['--'] + child + [str(binary)] + extra


def launch_direct(o: GamescopeOptions, executable: str, arguments: str,
                  flags: set[str] | None = None, mangohud_config: str = '') -> subprocess.Popen:
    argv = direct_command(o, executable, arguments, flags)
    for program in argv[:2]:
        if program == 'gamescope' and not detect_command('gamescope'):
            raise IntegrationError('Gamescope is not installed.')
    if o.gamemode and not detect_command('gamemoderun'):
        raise IntegrationError('GameMode launcher is not installed (gamemoderun missing).')
    if o.mangoapp and not detect_command('mangoapp'):
        raise IntegrationError('mangoapp is missing: install the mangoapp package.')
    env = os.environ.copy()
    env['DISABLE_AFMF'] = '1'
    if o.mangoapp and mangohud_config:
        env['MANGOHUD_CONFIG'] = mangohud_config
    try:
        return subprocess.Popen(argv, shell=False, env=env, start_new_session=True)
    except OSError as exc:
        raise IntegrationError(f'Game launch failed: {exc}') from exc


METRIC_KEYS = {
    'FPS': 'fps',
    'Frametime': 'frametime',
    'GPU temperature': 'gpu_temp',
    'GPU utilization': 'gpu_stats',
    'GPU clock': 'gpu_core_clock',
    'VRAM': 'vram',
    'CPU utilization': 'cpu_stats',
    'RAM': 'ram',
}


def mangohud_configuration(enabled_metrics: list[str], position: str, opacity: int) -> str:
    valid_positions = {'Top left': 'top-left', 'Top right': 'top-right',
                       'Bottom left': 'bottom-left', 'Bottom right': 'bottom-right'}
    if position not in valid_positions or not 20 <= opacity <= 100:
        raise IntegrationError('Invalid MangoHud position or opacity.')
    selected = set(enabled_metrics)
    if selected - METRIC_KEYS.keys():
        raise IntegrationError('Unsupported MangoHud metric.')
    # Disable all metrics that MangoHud otherwise enables by default.
    toggles = ['read_cfg'] + [f'{k}={1 if label in selected else 0}'
               for label, k in METRIC_KEYS.items()]
    toggles += [f'position={valid_positions[position]}', f'alpha={opacity / 100:.2f}',
                f'background_alpha={min(opacity / 100, 0.60):.2f}']
    return ','.join(toggles)


def mangohud_config_file(config_csv: str) -> str:
    return '# Generated by RyuSCOPE GS. Apply manually if desired.\n' + '\n'.join(config_csv.split(',')) + '\n'


LACT_SOCKET = '/run/lactd.sock'
LACT_READ_COMMANDS = {'ping', 'list_devices', 'device_info', 'device_stats',
                      'device_clocks_info', 'get_gpu_config'}


def lact_request(command: str, args: dict[str, Any] | None = None,
                 socket_path: str = LACT_SOCKET, timeout: float = 1.5) -> Any:
    """Only reads. No daemon config changes, no sudo, no set/confirm commands."""
    if command not in LACT_READ_COMMANDS:
        raise IntegrationError(f'LACT request blocked (read-only adapter): {command}')
    packet: dict[str, Any] = {'command': command}
    if args is not None:
        packet['args'] = args
    raw = (json.dumps(packet, separators=(',', ':')) + '\n').encode('utf-8')
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect(socket_path)
            s.sendall(raw)
            result = bytearray()
            while b'\n' not in result:
                chunk = s.recv(65536)
                if not chunk:
                    break
                result += chunk
                if len(result) > 2 * 1024 * 1024:
                    raise IntegrationError('LACT response exceeds 2 MiB limit.')
    except (OSError, TimeoutError) as exc:
        raise IntegrationError(f'Cannot read LACT daemon socket: {exc}') from exc
    try:
        payload = json.loads(bytes(result).split(b'\n', 1)[0])
    except (ValueError, IndexError) as exc:
        raise IntegrationError('Invalid response from LACT daemon.') from exc
    if not isinstance(payload, dict) or payload.get('status') != 'ok':
        raise IntegrationError('LACT returned error: ' + str(payload.get('data') if isinstance(payload, dict) else payload))
    return payload.get('data')


def lact_devices(socket_path: str = LACT_SOCKET) -> list[dict[str, Any]]:
    response = lact_request('list_devices', socket_path=socket_path)
    if not isinstance(response, list):
        raise IntegrationError('Unexpected LACT device list format.')
    return [device for device in response if isinstance(device, dict) and isinstance(device.get('id'), str)]


def lact_device_data(device_id: str, socket_path: str = LACT_SOCKET) -> dict[str, Any]:
    return {
        'info': lact_request('device_info', {'id': device_id}, socket_path=socket_path),
        'stats': lact_request('device_stats', {'id': device_id}, socket_path=socket_path),
        'config': lact_request('get_gpu_config', {'id': device_id}, socket_path=socket_path),
    }
