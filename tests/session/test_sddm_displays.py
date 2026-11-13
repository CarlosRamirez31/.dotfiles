import importlib.machinery
import importlib.util
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[2] / 'system/sddm/Xsetup'
loader = importlib.machinery.SourceFileLoader('sddm_displays', str(SCRIPT))
spec = importlib.util.spec_from_loader(loader.name, loader)
sddm = importlib.util.module_from_spec(spec)
loader.exec_module(sddm)


class SddmDisplays(unittest.TestCase):
    def configure(self, outputs, closed, active='', fail=False):
        calls = []

        def run(args):
            calls.append(args)
            if fail:
                raise subprocess.CalledProcessError(1, args)
            return subprocess.CompletedProcess(args, 0, active)

        with patch.object(sddm, 'connected', return_value=outputs), \
                patch.object(sddm, 'lid_closed', return_value=closed), \
                patch.object(sddm.time, 'sleep'), patch.object(sddm, 'run', side_effect=run):
            sddm.configure()
        return calls

    def test_closed_lid_enables_both_externals_before_disabling_panel(self):
        calls = self.configure(['eDP-1', 'DP-1-0', 'HDMI-1-0'], True,
                               'DP-1-0 connected primary 1920x1080+0+0\n')
        self.assertIn('--dryrun', calls[0])
        self.assertEqual(calls[1], ['xrandr', '--output', 'DP-1-0', '--auto', '--primary',
                                   '--pos', '0x0', '--output', 'HDMI-1-0', '--auto',
                                   '--right-of', 'DP-1-0'])
        self.assertEqual(calls[-1], ['xrandr', '--output', 'eDP-1', '--off'])

    def test_closed_lid_without_active_external_keeps_panel(self):
        calls = self.configure(['eDP-1', 'HDMI-1'], True)
        self.assertFalse(any('--off' in call for call in calls))

    def test_without_externals_even_closed_lid_keeps_internal_enabled(self):
        calls = self.configure(['eDP-1'], True)
        self.assertEqual(calls[-1], ['xrandr', '--output', 'eDP-1', '--auto',
                                     '--primary', '--pos', '0x0'])

    def test_open_lid_keeps_internal_alongside_external(self):
        calls = self.configure(['eDP-1', 'HDMI-1'], False)
        self.assertEqual(calls[-1][-5:], ['--output', 'eDP-1', '--auto', '--right-of', 'HDMI-1'])
        self.assertFalse(any('--off' in call for call in calls))

    def test_failed_activation_never_disables_internal(self):
        with self.assertRaises(subprocess.CalledProcessError):
            self.configure(['eDP-1', 'HDMI-1'], True, fail=True)

    def test_delayed_external_is_detected_before_panel_selection(self):
        with patch.object(sddm, 'connected', side_effect=[['eDP-1'], ['eDP-1', 'HDMI-1']]), \
                patch.object(sddm, 'lid_closed', return_value=True), \
                patch.object(sddm.time, 'sleep') as sleep, patch.object(sddm, 'run') as run:
            run.return_value.stdout = ''
            sddm.configure()
        sleep.assert_called_once_with(0.5)
        self.assertIn('HDMI-1', run.call_args_list[0].args[0])


if __name__ == '__main__':
    unittest.main()
