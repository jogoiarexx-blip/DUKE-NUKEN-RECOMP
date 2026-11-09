
"""Verify graphics presets without owning or loading commercial PS1 media."""
import copy
import io
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
import sys
import tempfile
import unittest

TOOLS = Path(__file__).resolve().parents[2] / 'tools' / 'local'
sys.path.insert(0, str(TOOLS))
import player_profiles as profiles
import run


class GraphicsPresetTest(unittest.TestCase):
    def test_validate_and_preserve_unrelated_options(self):
        for name in profiles.GRAPHICS_PRESETS:
            with self.subTest(name=name):
                profile = profiles.default_profile('modernized')
                profile['controls']['mouse_sensitivity'] = 0.33
                profile['controls']['sound_music'] = 48
                profile['controls']['controller_speed'] = 140
                profile['presentation']['window_width'] = 1280
                old = copy.deepcopy(profile)
                profiles.apply_graphics_preset(profile, name)
                self.assertEqual(profile['controls']['mouse_sensitivity'], 0.33)
                self.assertEqual(profile['controls']['sound_music'], 48)
                self.assertEqual(profile['controls']['controller_speed'], 140)
                self.assertEqual(profile['presentation']['window_width'], 1280)
                for key in old['controls']:
                    if key not in profiles.GRAPHICS_PRESET_VALUES[name]['controls']:
                        self.assertEqual(profile['controls'][key], old['controls'][key])
                profiles.validate_presentation(profile['presentation'])
                profiles.validate_controls(profile['controls'])

    def test_remastered_persists_and_cli_override_wins(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'profiles.json'
            with redirect_stdout(io.StringIO()):
                self.assertEqual(run.main(['--settings-file', str(path),
                             '--graphics-preset', 'remastered', '--internal-scale',
                             '2', '--texture-precision', 'original',
                             '--show-settings']), 0)
            data, _ = profiles.load(path)
            p = data['profiles']['modernized']
            self.assertEqual(p['presentation']['internal_scale'], 2)
            self.assertEqual(p['controls']['texture_precision'], 'original')
            self.assertEqual(p['controls']['geometry_precision'], 'corrected')
            self.assertEqual(p['controls']['dynamic_lights'], 'on')
            self.assertEqual(p['controls']['world_renderer'], 'polymorph')
            self.assertEqual(data['profiles']['vanilla'],
                             profiles.default_profile('vanilla'))

    def test_original_preset_does_not_reset_controls(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'profiles.json'
            data = profiles.defaults()
            data['profiles']['modernized']['controls']['mouse_sensitivity'] = 0.53
            profiles.save(path, data)
            with redirect_stdout(io.StringIO()):
                run.main(['--settings-file', str(path),
                          '--graphics-preset', 'original', '--show-settings'])
            updated, _ = profiles.load(path)
            controls = updated['profiles']['modernized']['controls']
            self.assertEqual(controls['mouse_sensitivity'], 0.53)
            self.assertEqual(controls['widescreen'], 'off')
            self.assertEqual(controls['dynamic_lights'], 'off')
            self.assertEqual(updated['profiles']['modernized']
                             ['presentation']['internal_scale'], 1)

    def test_vanilla_rejection_is_transactional(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'profiles.json'
            profiles.save(path, profiles.defaults())
            before = path.read_bytes()
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
                run.main(['--settings-file', str(path), '--vanilla',
                          '--graphics-preset', 'remastered', '--show-settings'])
            self.assertEqual(raised.exception.code, 2)
            self.assertEqual(path.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
