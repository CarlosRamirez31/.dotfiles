import importlib.machinery
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'dotfiles/.local/bin/dotfiles-power-profile'
loader = importlib.machinery.SourceFileLoader('power_profile', str(SCRIPT))
spec = importlib.util.spec_from_loader(loader.name, loader)
power = importlib.util.module_from_spec(spec)
loader.exec_module(power)

LISTING = ('eDP-2 connected primary 1920x1080+1920+0\n'
           '   1920x1080 144.00*+ 60.00 + 59.97\n'
           'HDMI-1-1 connected 1920x1080+0+0\n'
           '   1920x1080 60.00*+\n')


class PowerProfileTest(unittest.TestCase):
    def test_only_the_internal_panel_supplies_refresh_and_supported_rates(self):
        panel = power.panel(LISTING)
        self.assertEqual(panel['rate'], 144)
        self.assertEqual(panel['name'], 'eDP-2')
        self.assertIn(60, panel['rates'])

    def test_inactive_internal_panel_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, 'Activa la pantalla'):
            power.panel('eDP-2 connected\n  1920x1080 144.00+\n')

    def test_unsupported_refresh_is_rejected_before_changes(self):
        with patch.object(power, 'run', return_value='eDP-2 connected 1920x1080+0+0\n  1920x1080 60.00*\n') as run:
            with self.assertRaisesRegex(RuntimeError, '144 Hz'):
                power.apply('save-fluid')
        self.assertEqual(run.call_count, 1)

    def test_failed_brightness_rolls_back_profile_refresh_and_brightness(self):
        with tempfile.TemporaryDirectory() as directory:
            light = Path(directory)
            (light / 'brightness').write_text('800')
            (light / 'max_brightness').write_text('800')
            commands = []

            def run(*args):
                commands.append(args)
                if args == ('xrandr', '--current'):
                    return LISTING
                if args == ('powerprofilesctl', 'get'):
                    return 'balanced'
                return ''

            with patch.object(power, 'backlight', return_value=light), \
                    patch.object(power, 'run', side_effect=run), \
                    patch.object(power, 'set_rate') as rate, \
                    patch.object(power, 'set_brightness', side_effect=[RuntimeError('Permiso denegado'), None]) as brightness:
                with self.assertRaisesRegex(RuntimeError, 'restauraron'):
                    power.apply('save-max')
            self.assertEqual(rate.call_args_list[-1].args[1], 144)
            self.assertEqual(brightness.call_args_list[-1].args[1], 800)
            self.assertEqual(commands[-1], ('powerprofilesctl', 'set', 'balanced'))

    def test_success_requires_confirmed_hardware_settings(self):
        with tempfile.TemporaryDirectory() as directory:
            light = Path(directory)
            (light / 'brightness').write_text('800')
            (light / 'max_brightness').write_text('800')

            def run(*args):
                return LISTING if args == ('xrandr', '--current') else 'balanced'

            with patch.object(power, 'backlight', return_value=light), \
                    patch.object(power, 'run', side_effect=run), \
                    patch.object(power, 'set_rate'), patch.object(power, 'set_brightness'), \
                    patch.object(power, 'status', return_value={'active': 'bright'}):
                with self.assertRaisesRegex(RuntimeError, 'confirmar'):
                    power.apply('save-fluid')

if __name__ == '__main__':
    unittest.main()
