"""Read-only hardware and optional MangoHud CSV telemetry for RyuSCOPE GS.

No GPU tuning, no privileged APIs, no synthetic values. Missing measurements
remain None so callers can display N/A. The FPS value comes from an *active*
MangoHud CSV log, never from a guess based on refresh or frame limiter.
"""
from __future__ import annotations

import csv
import io
import math
import time
from dataclasses import dataclass
from pathlib import Path


DEFAULT_LOG_DIR = Path.home() / '.local' / 'share' / 'RyuSCOPE-GS' / 'MangoHud-Logs'


@dataclass(frozen=True)
class GPUSample:
    usage: float | None = None
    temperature_c: float | None = None
    clock_mhz: float | None = None
    vram_used_gib: float | None = None
    power_w: float | None = None
    card: str = ''


def _number(path: Path) -> float | None:
    try:
        value = float(path.read_text(encoding='ascii').strip())
        return value if math.isfinite(value) else None
    except (OSError, ValueError, UnicodeError):
        return None


def _clock_from_pp_dpm(path: Path) -> float | None:
    try:
        for line in path.read_text(encoding='ascii').splitlines():
            if '*' not in line:
                continue
            words = line.replace(':', ' ').split()
            for word in words:
                if word.lower().endswith('mhz'):
                    return float(word[:-3])
    except (OSError, ValueError, UnicodeError):
        pass
    return None


def read_gpu_sample(drm_root: Path = Path('/sys/class/drm')) -> GPUSample:
    """Select a readable AMD GPU, preferring one exposing busy counters."""
    candidates = []
    try:
        cards = sorted(drm_root.glob('card[0-9]*'))
    except OSError:
        cards = []
    for card in cards:
        if not card.name[4:].isdigit():
            continue
        device = card / 'device'
        try:
            vendor = (device / 'vendor').read_text(encoding='ascii').strip().lower()
            if vendor != '0x1002':
                continue
        except (OSError, UnicodeError):
            continue
        usage = _number(device / 'gpu_busy_percent')
        hwmon_list = list((device / 'hwmon').glob('hwmon*')) if (device / 'hwmon').exists() else []
        hwmon = None
        for candidate in hwmon_list:
            try:
                if (candidate / 'name').read_text(encoding='ascii').strip() == 'amdgpu':
                    hwmon = candidate
                    break
            except (OSError, UnicodeError):
                continue
        if hwmon is None and hwmon_list:
            hwmon = hwmon_list[0]
        temp_raw = _number(hwmon / 'temp1_input') if hwmon else None
        temp = temp_raw / 1000 if temp_raw is not None else None
        freq_hz = _number(hwmon / 'freq1_input') if hwmon else None
        clock = freq_hz / 1_000_000 if freq_hz is not None else _clock_from_pp_dpm(device / 'pp_dpm_sclk')
        used = _number(device / 'mem_info_vram_used')
        power = _number(hwmon / 'power1_average') if hwmon else None
        sample = GPUSample(
            usage=usage if usage is not None and 0 <= usage <= 100 else None,
            temperature_c=temp if temp is not None and -20 <= temp <= 150 else None,
            clock_mhz=clock if clock is not None and 0 <= clock <= 10000 else None,
            vram_used_gib=used / (1024 ** 3) if used is not None and used >= 0 else None,
            power_w=power / 1_000_000 if power is not None and power >= 0 else None,
            card=card.name,
        )
        vram_total = _number(device / 'mem_info_vram_total') or 0
        candidates.append((int(sample.usage is not None) + int(sample.temperature_c is not None),
                           vram_total, sample))
    return max(candidates, key=lambda item: (item[0], item[1]))[2] if candidates else GPUSample()


def _fps_from_csv(path: Path) -> float | None:
    """Inspect a bounded tail of a MangoHud log, with a real CSV header."""
    try:
        size = path.stat().st_size
        if not 0 < size <= 500_000_000:
            return None
        with path.open('rb') as f:
            head = f.read(min(size, 96_000)).decode('utf-8-sig', errors='replace')
            header = None
            for line in head.splitlines():
                try:
                    columns = [c.strip().lower() for c in next(csv.reader([line]))]
                except (csv.Error, StopIteration):
                    continue
                if 'fps' in columns and len(columns) >= 2:
                    header = columns.index('fps')
                    break
            if header is None:
                return None
            f.seek(max(0, size - 96_000))
            tail = f.read().decode('utf-8', errors='replace')
        if size > 96_000:
            tail = tail.split('\n', 1)[-1]  # Skip potentially truncated first record.
        for line in reversed(tail.splitlines()[-100:]):
            try:
                cells = next(csv.reader([line]))
                if len(cells) <= header:
                    continue
                value = float(cells[header])
                if math.isfinite(value) and 0 < value < 1200:
                    return value
            except (csv.Error, StopIteration, ValueError, IndexError):
                continue
    except (OSError, UnicodeError):
        return None
    return None


def read_live_fps(directory: Path = DEFAULT_LOG_DIR, *, max_age_s: float = 8.0,
                  now: float | None = None) -> float | None:
    """Return last actual FPS sample from a currently growing/recent CSV log."""
    if now is None:
        now = time.time()
    try:
        files = ((p.stat().st_mtime, p) for p in directory.glob('*.csv') if p.is_file())
        latest = max(files, key=lambda pair: pair[0], default=None)
    except OSError:
        return None
    if not latest or latest[0] < now - max_age_s or latest[0] > now + 30:
        return None
    return _fps_from_csv(latest[1])


def format_reading(value: float | None, *, digits: int = 0) -> str:
    if value is None:
        return 'N/A'
    return f'{value:.{digits}f}'
