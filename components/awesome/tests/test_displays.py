"""Run with python3 -m unittest discover -s components/awesome/tests."""
import copy
import importlib.machinery
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'dotfiles/.local/bin/dotfiles-display'
loader = importlib.machinery.SourceFileLoader('displays', str(SCRIPT))
spec = importlib.util.spec_from_loader(loader.name, loader)
displays = importlib.util.module_from_spec(spec)
loader.exec_module(displays)


def fixture(count=20):
    return '\n'.join(f'DP-{i} connected ' + ('primary 1920x1080+0+0' if i == 0 else '') +
                     '\n   1920x1080 60.00' for i in range(count))


def outputs(count=20):
    with patch.object(displays.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, fixture(count))):
        return displays.query()


class DisplaysTest(unittest.TestCase):
    def test_modes_sorted_by_maximum_resolution_without_duplicates(self):
        listing = ('DP-0 connected primary 1920x1080+0+0\n'
                   '   1920x1080 60.00*\n'
                   '   1280x720 60.00\n'
                   '   3840x2160 30.00\n'
                   '   2560x1440 60.00\n'
                   '   3840x2160 60.00\n')
        with patch.object(displays.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, listing)):
            detected = displays.query()[0]
        self.assertEqual(detected['modes'], ['3840x2160', '2560x1440', '1920x1080', '1280x720'])
        self.assertEqual(detected['mode'], '1920x1080')

    def test_twenty_outputs_and_disconnected_output(self):
        with patch.object(displays.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, fixture() + '\nHDMI-1 disconnected\n')):
            detected = displays.query()
        self.assertEqual(len(detected), 20)
        self.assertTrue(detected[0]['primary'])
        self.assertFalse(detected[-1]['enabled'])

    def test_hotplug_extends_all_twenty_without_overlap(self):
        detected = outputs()
        with patch.object(displays, 'load', return_value={}), patch.object(displays, 'query', return_value=copy.deepcopy(detected)), patch.object(displays, 'apply') as apply:
            displays.automatic(detected)
        configured = apply.call_args.args[0]
        self.assertTrue(all(o['enabled'] for o in configured))
        self.assertEqual([o['x'] for o in configured], [i*1920 for i in range(20)])

    def test_negative_positions_normalize_and_primary_is_enabled(self):
        detected = outputs(2)
        detected[0].update(enabled=False, primary=True)
        detected[1].update(enabled=True, mode='1920x1080', x=-1920, y=-1080)
        result = displays.normalize(detected)
        self.assertEqual((result[1]['x'], result[1]['y']), (0, 0))
        self.assertTrue(result[1]['primary'])
        self.assertFalse(result[0]['primary'])

    def test_all_off_rejected_before_xrandr(self):
        detected = outputs(1)
        detected[0]['enabled'] = False
        with patch.object(displays.subprocess, 'run') as run:
            with self.assertRaises(ValueError):
                displays.apply(detected)
            run.assert_not_called()

    def test_dryrun_rejects_hardware_limit_before_applying(self):
        detected = outputs()
        with patch.object(displays.subprocess, 'run', side_effect=subprocess.CalledProcessError(1, 'xrandr')) as run:
            with self.assertRaises(subprocess.CalledProcessError):
                displays.apply(detected)
        self.assertEqual(run.call_count, 1)
        self.assertIn('--dryrun', run.call_args.args[0])

    def test_saved_layout_preserves_disabled_outputs(self):
        detected = outputs(2)
        stored = copy.deepcopy(detected)
        stored[1].update(mode='1920x1080', enabled=False)
        with tempfile.TemporaryDirectory() as directory, patch.object(displays, 'CONFIG', Path(directory)/'displays.json'):
            displays.save(stored)
            with patch.object(displays, 'query', return_value=copy.deepcopy(detected)), patch.object(displays, 'apply'):
                displays.automatic(detected)
            self.assertFalse(detected[1]['enabled'])

    def test_apply_builds_arguments_for_every_output(self):
        detected = outputs()
        for i, output in enumerate(detected):
            output.update(enabled=True, mode='1920x1080', x=i*1920)
        with patch.object(displays.subprocess, 'run') as run, patch.object(displays, 'refresh_bar'):
            displays.apply(detected)
        self.assertEqual(run.call_count, 2)
        self.assertEqual(run.call_args.args[0].count('--output'), 20)


if __name__ == '__main__':
    unittest.main()
