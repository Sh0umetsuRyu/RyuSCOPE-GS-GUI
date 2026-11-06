"""Run AFMF's headless pixel checks through the packaged implicit manifest.

Requires the pinned upstream source, C compiler, Vulkan development files,
and a Vulkan ICD with VK_EXT_headless_surface. VK_DRIVER_FILES may select it.
"""
import argparse
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

from plugins import ryufg


def make_probe(source, work, headers):
    tests = source / 'tests'
    for file in tests.glob('headless*.[ch]'):
        shutil.copy2(file, work)
    main = work / 'headless.c'
    instance = work / 'headless_instance.c'
    # Remove the upstream explicit-layer requirement so discovery depends on
    # Vulkan's implicit loader and our actual packaged activation manifest.
    text, count = re.subn(r'    if \(!instance_layer_available\(LAYER_NAME\)\) \{.*?\n    \}\n',
                          '', main.read_text(), count=1, flags=re.S)
    if count != 1:
        raise RuntimeError('Unexpected upstream headless probe source')
    main.write_text(text)
    instance.write_text(instance.read_text().replace(
        'const char *layers[2] = {LAYER_NAME, VALIDATION_LAYER_NAME};',
        'const char *layers[] = {VALIDATION_LAYER_NAME};').replace(
        'with_validation ? 2u : 1u', 'with_validation ? 1u : 0u'))
    probe = work / 'probe'
    include = ['-I', str(headers)] if headers else []
    subprocess.run(['cc', '-std=gnu11', '-D_POSIX_C_SOURCE=200809L', *include,
                    *map(str, sorted(work.glob('*.c'))), '-lvulkan', '-o', str(probe)],
                   check=True)
    return probe


def run_probe(command, env, log, *, enabled):
    result = subprocess.run(command, env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, timeout=45)
    log.write_text(result.stdout)
    print(f'{log.stem}: {log}', flush=True)
    generated = '119 generated' in result.stdout
    if result.returncode or generated != enabled:
        raise RuntimeError(result.stdout)
    if not enabled and '[AFMF ' in result.stdout:
        raise RuntimeError('AFMF ran while disabled\n' + result.stdout)
    print(next((line for line in result.stdout.splitlines() if '119 generated' in line),
               'No AFMF activity'), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--headers', type=Path)
    parser.add_argument('--logs', type=Path, default=Path('build/ryufg-smoke-logs'))
    args = parser.parse_args()
    args.logs.mkdir(parents=True, exist_ok=True)
    logs = args.logs.resolve()
    with tempfile.TemporaryDirectory(prefix='RyuFG relocated ') as temporary:
        work = Path(temporary)
        probe = make_probe(args.source, work, args.headers)
        bundle = work / 'layer files'
        shutil.copytree(ryufg.payload(), bundle)
        env = {key: os.environ[key] for key in ('PATH', 'VK_DRIVER_FILES', 'VK_ICD_FILENAMES')
               if key in os.environ}
        env.update(HOME=str(work), XDG_DATA_HOME=str(work / 'xdg'),
                   AFMF_LOG='3', AFMF_TEST_FRAME_MS='2', AFMF_MIN_FPS='0',
                   AFMF_GOVERNOR='0', AFMF_ACQUIRE_TIMEOUT_US='16000')
        with patch.dict(os.environ, env, clear=True), patch.object(ryufg, 'payload', return_value=bundle):
            direct = ryufg.game_prefix(True, gamescope=False)
            run_probe([*direct, probe], env | {'AFMF_DUMP_DIR': str(work / 'direct')},
                      logs / 'relocated-direct.log', enabled=True)
            run_probe([probe], env | {'VK_ADD_IMPLICIT_LAYER_PATH': str(bundle), 'AFMF_ENABLE': '1'},
                      logs / 'default-off.log', enabled=False)
            run_probe([probe], env | {'VK_ADD_IMPLICIT_LAYER_PATH': str(bundle), 'AFMF_ENABLE': '1',
                                     ryufg.GATE: '1', 'DISABLE_AFMF': '1'},
                      logs / 'explicit-off.log', enabled=False)
            ryufg.prepare_steam()
            steam = ryufg.game_prefix(True, steam=True)
            run_probe([*steam, probe], env | {'AFMF_TEST_EXTRA_IMAGES': '5',
                                             'AFMF_DUMP_DIR': str(work / 'steam')},
                      logs / 'steam-style-discovery.log', enabled=True)


if __name__ == '__main__':
    main()
