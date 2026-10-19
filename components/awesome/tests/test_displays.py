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
    def row(self, count=3):
        detected = outputs(count)
        for i, output in enumerate(detected):
            output.update(enabled=True, mode='1920x1080', x=1920*i, y=0)
        return detected

    def test_reordering_row_keeps_all_monitors_adjacent(self):
        detected = self.row()
        detected[2].update(x=-1600, y=40)
        displays.snap_output(detected, detected[2], 0)
        displays.validate_layout(detected)
        ordered = sorted(detected, key=lambda o: o['x'])
        self.assertEqual([o['name'] for o in ordered], ['DP-2', 'DP-0', 'DP-1'])
        self.assertEqual([o['x']-ordered[0]['x'] for o in ordered], [0, 1920, 3840])

    def hybrid(self):
        detected = self.row()
        detected[0]['name'] = 'eDP-1'
        for o in detected:
            o['rate'] = '60.00'
        return detected

    def test_hybrid_change_rebuilds_framebuffer_with_external_outputs_off_together(self):
        before = self.hybrid()
        target = copy.deepcopy(before)
        target[1]['x'], target[2]['x'] = target[2]['x'], target[1]['x']
        with patch.object(displays, 'query', return_value=before), patch.object(displays.subprocess, 'run') as run, patch.object(displays, 'desktop_state') as state, patch.object(displays, 'refresh_bar'):
            displays.apply(target)
        commands = [call.args[0] for call in run.call_args_list]
        self.assertEqual(len(commands), 4)
        self.assertIn('--dryrun', commands[0])
        self.assertEqual(commands[1].count('--off'), 2)
        self.assertEqual(commands[2], ['xrandr', '--fb', '1920x1080'])
        self.assertNotIn('--off', commands[3])
        self.assertEqual(commands[3].count('--mode'), 3)
        self.assertEqual(commands[3].count('--rate'), 3)
        self.assertEqual(state.call_args_list[0].kwargs, {})
        self.assertEqual(state.call_args_list[1].kwargs, {'restore': True})
        self.assertEqual(before[1]['x'], 1920)

    def test_rebuild_failure_restores_previous_positions_using_same_recovery(self):
        before = self.hybrid()
        target = copy.deepcopy(before)
        target[1]['x'], target[2]['x'] = target[2]['x'], target[1]['x']
        results = [None, None, None, subprocess.CalledProcessError(1, 'xrandr'), None, None, None]
        with patch.object(displays, 'query', return_value=before), patch.object(displays.subprocess, 'run', side_effect=results) as run, patch.object(displays, 'desktop_state'), patch.object(displays, 'refresh_bar'):
            with self.assertRaisesRegex(ValueError, 'se restauró'):
                displays.apply(target)
        commands = [call.args[0] for call in run.call_args_list]
        self.assertEqual(commands[4].count('--off'), 2)
        self.assertEqual(commands[5], ['xrandr', '--fb', '1920x1080'])
        self.assertEqual(commands[6], displays.layout_args(before))

    def test_recovery_restores_even_if_framebuffer_shrink_fails(self):
        before = self.hybrid()
        results = [None, None, subprocess.CalledProcessError(1, 'xrandr'), None, None, None]
        with patch.object(displays, 'query', return_value=before), patch.object(displays.subprocess, 'run', side_effect=results) as run, patch.object(displays, 'desktop_state'), patch.object(displays, 'refresh_bar'):
            with self.assertRaisesRegex(ValueError, 'se restauró'):
                displays.apply(before)
        self.assertEqual(run.call_args_list[-1].args[0], displays.layout_args(before))

    def test_rate_is_not_reused_after_resolution_change(self):
        before = self.hybrid()
        target = copy.deepcopy(before)
        target[2].update(mode='1280x720', modes=['1920x1080', '1280x720'])
        with patch.object(displays, 'query', return_value=before), patch.object(displays.subprocess, 'run') as run, patch.object(displays, 'desktop_state'), patch.object(displays, 'refresh_bar'):
            displays.apply(target)
        final = run.call_args.args[0]
        last_output = final[final.index('DP-2'):]
        self.assertNotIn('--rate', last_output)

    def test_closed_lid_target_returns_internal_screen_to_off_after_reset(self):
        before = self.hybrid()
        target = copy.deepcopy(before)
        target[0].update(enabled=False, primary=False)
        target[1].update(x=0, primary=True)
        target[2]['x'] = 1920
        with patch.object(displays, 'query', return_value=before), patch.object(displays.subprocess, 'run') as run, patch.object(displays, 'desktop_state'), patch.object(displays, 'refresh_bar'):
            displays.apply(target)
        final = run.call_args.args[0]
        self.assertEqual(final[1:4], ['--output', 'eDP-1', '--off'])

    def test_gap_rejected_before_hardware_changes(self):
        detected = self.row(2)
        detected[1]['x'] += 100
        with patch.object(displays.subprocess, 'run') as run:
            with self.assertRaisesRegex(ValueError, 'hueco'):
                displays.apply(detected)
        run.assert_not_called()

    def test_partial_overlap_rejected(self):
        detected = self.row(2)
        detected[1]['x'] = 1500
        with self.assertRaisesRegex(ValueError, 'superpuestas'):
            displays.validate_layout(detected)

    def test_mirror_and_vertical_layout_are_valid(self):
        detected = self.row(2)
        detected[1].update(x=0, y=0)
        displays.validate_layout(detected)
        detected[1]['y'] = 1080
        displays.validate_layout(detected)

    def test_diagonal_corner_alone_does_not_connect_screens(self):
        detected = self.row(2)
        detected[1]['y'] = 1080
        with self.assertRaisesRegex(ValueError, 'hueco'):
            displays.validate_layout(detected)

    def test_closed_lid_in_middle_of_row_does_not_leave_gap(self):
        detected = self.row()
        detected[1]['name'] = 'eDP-1'
        with patch.object(displays, 'lid_closed', return_value=True), patch.object(displays, 'load', return_value={}), patch.object(displays, 'query', return_value=copy.deepcopy(detected)), patch.object(displays, 'apply'):
            displays.automatic(detected)
        displays.validate_layout(detected)
        self.assertEqual(detected[2]['x'] - detected[0]['x'], 1920)

    def test_lid_policy_reads_effective_overrides_and_ac_fallback(self):
        listing = ('# HandleLidSwitch=poweroff\n[Login]\nHandleLidSwitch=suspend\n'
                   '[Other]\nHandleLidSwitch=poweroff\n'
                   '[Login]\nHandleLidSwitch=lock\nHandleLidSwitchDocked=ignore\n')
        with patch.object(displays.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, listing)):
            self.assertEqual(displays.lid_policy(), ['lock', 'lock', 'ignore'])

    def test_graphical_lid_save_sends_password_through_stdin(self):
        actions = ['suspend', 'suspend', 'ignore']
        with patch.object(displays.subprocess, 'run') as run, patch.object(displays, 'lid_policy', return_value=actions):
            displays.configure_lid(actions, password='test-password')
        self.assertEqual(run.call_count, 2)
        for call in run.call_args_list:
            self.assertNotIn('test-password', call.args[0])
            self.assertEqual(call.kwargs['input'], 'test-password\n')
        self.assertIn('install', run.call_args_list[0].args[0])
        self.assertIn('--signal=HUP', run.call_args_list[1].args[0])

    def test_closed_lid_leaves_two_external_outputs(self):
        detected = outputs(3)
        detected[0]['name'] = 'eDP-1'
        with patch.object(displays, 'lid_closed', return_value=True), patch.object(displays, 'load', return_value={}), patch.object(displays, 'query', return_value=copy.deepcopy(detected)), patch.object(displays, 'apply') as apply:
            displays.automatic(detected)
        configured = apply.call_args.args[0]
        self.assertFalse(configured[0]['enabled'])
        self.assertEqual(sum(o['enabled'] for o in configured), 2)
        self.assertTrue(configured[1]['primary'])
        self.assertEqual([o['x'] for o in configured[1:]], [0, 1920])

    def test_closed_lid_without_external_keeps_internal(self):
        detected = outputs(1)
        detected[0]['name'] = 'eDP-1'
        with patch.object(displays, 'lid_closed', return_value=True):
            self.assertFalse(displays.docked(detected))

    def test_lid_option_can_be_disabled(self):
        with tempfile.TemporaryDirectory() as directory:
            options = Path(directory) / 'options.json'
            options.write_text('{"external_only_when_closed": false}')
            with patch.object(displays, 'OPTIONS', options), patch.object(displays, 'lid_closed', return_value=True):
                self.assertFalse(displays.docked(outputs(2)))

    def test_closed_and_open_lid_use_separate_profiles(self):
        detected = outputs(2)
        detected[0]['name'] = 'eDP-1'
        with patch.object(displays, 'lid_closed', return_value=False):
            opened = displays.key(detected)
        with patch.object(displays, 'lid_closed', return_value=True):
            closed = displays.key(detected)
        self.assertNotEqual(opened, closed)

    def test_opening_lid_enables_internal_again(self):
        detected = outputs(2)
        detected[0].update(name='eDP-1', enabled=False, primary=False)
        detected[1].update(enabled=True, primary=True, mode='1920x1080')
        with patch.object(displays, 'lid_closed', return_value=False), patch.object(displays, 'load', return_value={}), patch.object(displays, 'query', return_value=copy.deepcopy(detected)), patch.object(displays, 'apply'):
            displays.automatic(detected)
        self.assertTrue(detected[0]['enabled'])

    def test_invalid_lid_policy_does_not_run_sudo(self):
        with patch.object(displays.subprocess, 'run') as run:
            with self.assertRaises(ValueError):
                displays.configure_lid(['suspend', 'suspend', 'unknown'])
        run.assert_not_called()

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
        with patch.object(displays.subprocess, 'run') as run, patch.object(displays, 'query', return_value=copy.deepcopy(detected)), patch.object(displays, 'refresh_bar'):
            displays.apply(detected)
        self.assertEqual(run.call_count, 2)
        self.assertEqual(run.call_args.args[0].count('--output'), 20)


if __name__ == '__main__':
    unittest.main()
