import json
import os
import shlex
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from integrations import GamescopeOptions, OPTIONAL, REQUIRED, launch_direct, steam_launch_options
from plugins import ryufg
from steam_profile import apply_profile, preview_profile, restore_profile, SteamProfileError


class RyuFGSmoke(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory(prefix='ryufg smoke ')))
        self.payload = self.root / 'relocated payload'
        shutil.copytree(ryufg.payload(), self.payload)
        self.enterContext(patch.object(ryufg, 'payload', return_value=self.payload))
        self.enterContext(patch.dict(os.environ, {
            'HOME': str(self.root), 'XDG_DATA_HOME': str(self.root / 'data'),
            'PATH': str(self.root) + ':/usr/bin:/bin',
        }, clear=True))
        self.make_executable('gamescope', """#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
Path(os.environ['HOME'], 'compositor').write_text(json.dumps([dict(os.environ), sys.argv]))
child = sys.argv[sys.argv.index('--') + 1:]
os.execvpe(child[0], child, os.environ)
""")
        self.make_executable('mangoapp', '#!/bin/sh\nexit 0\n')
        self.game = self.make_executable('native game', """#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
Path(os.environ['HOME'], 'game').write_text(json.dumps([dict(os.environ), sys.argv]))
""")
        self.config = self.root / 'localconfig.vdf'
        self.original = (
            '"UserLocalConfigStore" { "Software" { "Valve" { "Steam" { "apps" {\n'
            ' "42" { "LaunchOptions" "mangohud %command%" }\n'
            ' "43" { "LaunchOptions" "other %command%" }\n'
            '} } } } }\n'
        )
        self.config.write_text(self.original)
        self.state = self.root / 'state.json'
        self.flags = REQUIRED | OPTIONAL
        self.options = GamescopeOptions(ryufg=True, mangoapp=True, scaling='FSR (Gamescope built-in)')

    def make_executable(self, name, contents):
        path = self.root / name
        path.write_text(contents)
        path.chmod(0o755)
        return path

    def observed(self, file):
        return json.loads((self.root / file).read_text())

    def assert_scoped(self):
        compositor, args = self.observed('compositor')
        game, game_args = self.observed('game')
        self.assertEqual(compositor['DISABLE_AFMF'], '1')
        self.assertNotIn(ryufg.GATE, compositor)
        self.assertNotIn('DISABLE_AFMF', game)
        self.assertEqual(game[ryufg.GATE], '1')
        self.assertEqual(game['AFMF_ENABLE'], '1')
        self.assertEqual(game['AFMF_GAMESCOPE'], '1')
        self.assertEqual(compositor['MANGOHUD_CONFIG'], 'fps=1')
        self.assertIn('--mangoapp', args)
        self.assertEqual(args[args.index('-F') + 1], 'fsr')
        self.assertEqual(game_args[1:], ['arg with spaces'])
        return game

    def test_direct(self):
        os.environ['VK_ADD_IMPLICIT_LAYER_PATH'] = str(self.root / 'other layers')
        process = launch_direct(self.options, str(self.game), "'arg with spaces'", self.flags, 'fps=1')
        self.assertEqual(process.wait(timeout=10), 0)
        self.assertEqual(self.assert_scoped()['VK_ADD_IMPLICIT_LAYER_PATH'],
                         f"{self.payload}:{os.environ['VK_ADD_IMPLICIT_LAYER_PATH']}")

    def test_legacy_profile_defaults_off(self):
        os.environ.update(AFMF_ENABLE='1', RYUSCOPE_RYUFG='1')
        process = launch_direct(GamescopeOptions(), str(self.game), '', self.flags)
        self.assertEqual(process.wait(timeout=10), 0)
        game, _ = self.observed('game')
        self.assertEqual(game['DISABLE_AFMF'], '1')
        self.assertFalse(ryufg.registered_manifest().exists())

    def test_steam_apply_execute_and_restore(self):
        _, proposed, _ = preview_profile(self.config, 42, self.options, self.flags,
                                          mango_config='fps=1', state_path=self.state)
        self.assertFalse(ryufg.registered_manifest().exists())
        options, _ = apply_profile(self.config, 42, self.options, self.flags,
                                   mango_config='fps=1', state_path=self.state, running=lambda: False)
        self.assertEqual(proposed, options)
        self.assertIn('"other %command%"', self.config.read_text())
        proton = self.make_executable('Proton stand-in', '#!/bin/sh\nexec "$@"\n')
        command = shlex.join([str(proton), str(self.game), 'arg with spaces'])
        subprocess.run(['/bin/sh', '-c', options.replace('%command%', command)], check=True, timeout=10)
        self.assertNotIn('VK_ADD_IMPLICIT_LAYER_PATH', self.assert_scoped())
        manifest = json.loads(ryufg.registered_manifest().read_text())
        self.assertEqual(Path(manifest['layer']['library_path']).read_bytes(),
                         (self.payload / ryufg.LIBRARY).read_bytes())
        ryufg.prepare_steam()
        restore_profile(self.config, 42, state_path=self.state, running=lambda: False)
        self.assertIn('"mangohud %command%"', self.config.read_text())

    def test_copied_steam_command(self):
        options = steam_launch_options(self.options, self.flags, 'fps=1')
        command = shlex.join([str(self.game), 'arg with spaces'])
        subprocess.run(['/bin/sh', '-c', options.replace('%command%', command)], check=True, timeout=10)
        self.assert_scoped()

    def test_conflicts(self):
        self.config.write_text(self.original.replace('mangohud %command%', 'AFMF_ENABLE=1 %command%'))
        with self.assertRaisesRegex(SteamProfileError, 'conflicting'):
            preview_profile(self.config, 42, self.options, self.flags, state_path=self.state)
        manifest = ryufg.registered_manifest().with_name('other.json')
        manifest.parent.mkdir(parents=True)
        manifest.write_text(json.dumps({'layer': {'name': 'VK_LAYER_LS_frame_generation'}}))
        with self.assertRaisesRegex(ryufg.RyuFGError, 'Conflicting implicit'):
            ryufg.game_prefix(True)
        manifest.write_text(json.dumps({'layer': {'name': ryufg.LAYER}}))
        with self.assertRaisesRegex(ryufg.RyuFGError, 'Another AFMF'):
            ryufg.game_prefix(True)


if __name__ == '__main__':
    unittest.main()
