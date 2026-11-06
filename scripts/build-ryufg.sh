#!/usr/bin/env bash
# Build the pinned, unmodified AFMF source and stage a relocatable RyuFG payload.
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
revision=e738127530ebf4a8b070b9fb38469377958120a7
source_dir="${AFMF_SOURCE_DIR:-$root/build/afmf-linux}"
build_dir="$root/build/afmf-linux-build"
[[ "$(uname -sm)" == 'Linux x86_64' ]] || { echo 'RyuFG requires x86-64 Linux.' >&2; exit 2; }
if [[ ! -d "$source_dir/.git" ]]; then
    git clone https://github.com/serialexperimentslainnnn/afmf-linux.git "$source_dir"
    git -C "$source_dir" checkout --detach "$revision"
fi
[[ "$(git -C "$source_dir" rev-parse HEAD)" == "$revision" &&
   -z "$(git -C "$source_dir" status --porcelain)" ]] || {
    echo "Use a clean AFMF-Linux checkout at $revision." >&2; exit 2;
}
cmake -S "$source_dir" -B "$build_dir" -G Ninja -DCMAKE_BUILD_TYPE=Release "$@"
cmake --build "$build_dir"
python3 - "$source_dir" "$build_dir" "$root/build/ryufg" "$revision" <<'PY'
import json
import shutil
import sys
from pathlib import Path

source, build, target = map(Path, sys.argv[1:4])
target.mkdir(parents=True, exist_ok=True)
document = json.loads((build / 'layer/afmf-linux.json').read_text())
document['layer']['library_path'] = './libafmf-linux.so'
document['layer']['enable_environment'] = {'RYUSCOPE_RYUFG': '1'}
shutil.copy2(build / 'layer/libafmf-linux.so', target)
shutil.copyfile(source / 'LICENSE', target / 'LICENSE-AFMF.txt')
shutil.copyfile(source / 'shaders/fidelityfx/LICENSE.txt', target / 'LICENSE-FidelityFX.txt')
(target / 'UPSTREAM.txt').write_text(
    f'AFMF-Linux v1.3.1\nhttps://github.com/serialexperimentslainnnn/afmf-linux/tree/{sys.argv[4]}\n'
    'RyuFG changes the manifest activation gate and uses a relative library path.\n'
)
(target / 'ryuscope-ryufg.json').write_text(json.dumps(document, indent=2) + '\n')
PY
printf 'RyuFG payload staged at %s/build/ryufg\n' "$root"
