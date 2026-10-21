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
    def test_unchanged_automatic_checks_do_not_probe_hardware_or_apply_layout(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, 'dotfiles-display-topology').write_text('DP-0')
            result = subprocess.CompletedProcess([], 0, fixture(1))
            with patch.dict(displays.os.environ, {'XDG_RUNTIME_DIR': directory}), \
                    patch.object(displays.sys, 'argv', ['dotfiles-display', '--auto']), \
                    patch.object(displays, 'hardware_topology', return_value='connected'), \
                    patch.object(displays, 'disable_disconnected_outputs', return_value=False), \
                    patch.object(displays, 'docked', return_value=False), \
                    patch.object(displays, 'automatic') as automatic, \
                    patch.object(displays.subprocess, 'run', return_value=result) as run:
                displays.main()
                displays.main()
            self.assertEqual(len(run.call_args_list), 1)
            for call in run.call_args_list:
                self.assertEqual(call.args[0], ['xrandr', '--query', '--verbose'])
            automatic.assert_not_called()

    def test_connector_change_invalidates_automatic_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.CompletedProcess([], 0, fixture(1))
            with patch.dict(displays.os.environ, {'XDG_RUNTIME_DIR': directory}), \
                    patch.object(displays.sys, 'argv', ['dotfiles-display', '--auto']), \
                    patch.object(displays, 'hardware_topology', side_effect=['old', 'new']), \
                    patch.object(displays, 'disable_disconnected_outputs', return_value=False), \
                    patch.object(displays, 'docked', return_value=False), \
                    patch.object(displays, 'automatic'), \
                    patch.object(displays.subprocess, 'run', return_value=result) as run:
                displays.main()
                displays.main()
            self.assertEqual(len(run.call_args_list), 2)
            self.assertEqual(Path(directory, 'dotfiles-display-hardware-topology').read_text(), 'apps-scale-v6:new')

    def test_unplugged_active_output_is_disabled_without_touching_connected_monitors(self):
        listing = ('eDP-2 connected primary 1920x1080+1920+0\n'
                   'HDMI-1-1 disconnected 1920x1080+0+0\n'
                   'DP-1-1 disconnected\n'
                   'DP-2 connected 1920x1080+3840+0\n')
        result = subprocess.CompletedProcess([], 0, listing)
        with patch.object(displays.subprocess, 'run', return_value=result) as run:
            self.assertTrue(displays.disable_disconnected_outputs())
        self.assertEqual(run.call_args_list[-1].args[0],
                         ['xrandr', '--current', '--output', 'HDMI-1-1', '--off'])

    def test_disconnected_cleanup_requires_a_visible_connected_anchor(self):
        result = subprocess.CompletedProcess([], 0, 'HDMI-1-1 disconnected 1920x1080+0+0\n')
        with patch.object(displays.subprocess, 'run', return_value=result) as run:
            self.assertFalse(displays.disable_disconnected_outputs())
        self.assertEqual(run.call_count, 1)

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

    def test_small_vertical_offset_is_preserved_when_snapping_row(self):
        detected = self.row()
        detected[0]['y'] = 80
        displays.snap_output(detected, detected[0], 0)
        self.assertEqual(detected[0]['y'], 80)
        self.assertEqual([o['y'] for o in detected[1:]], [0, 0])
        displays.validate_layout(detected)

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
        target[2].pop('rate')
        before[2]['modes'].append('1280x720')
        before[2]['rates']['1280x720'] = ['60.00']
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

    def test_each_monitor_keeps_its_own_modes_rates_and_identity(self):
        listing = ('DP-0 connected primary 3840x2160+0+0\n'
                   '\tEDID:\n\t\t' + 'ab'*16 + '\n'
                   '   3840x2160 59.94*+ 30.00\n'
                   '   1920x1080 120.00 60.00\n'
                   'HDMI-0 connected 1920x1080+3840+0\n'
                   '\tEDID:\n\t\t' + 'cd'*16 + '\n'
                   '   1920x1080 75.00*+ 60.00\n')
        with patch.object(displays.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, listing)):
            a, b = displays.query()
        self.assertEqual(a['modes'][0], '3840x2160')
        self.assertEqual(b['modes'], ['1920x1080'])
        self.assertEqual(a['rate'], '59.94')
        self.assertEqual(b['rates']['1920x1080'], ['75.00', '60.00'])
        self.assertNotEqual(a['identity'], b['identity'])
        self.assertNotEqual(displays.key([a]), displays.key([dict(a, identity=b['identity'])]))

    def test_selected_frequency_is_applied_including_dryrun(self):
        before = self.row(1)
        before[0].update(rate='60.00', rates={'1920x1080': ['144.00', '60.00']})
        target = copy.deepcopy(before)
        target[0]['rate'] = '144.00'
        with patch.object(displays, 'query', return_value=before), patch.object(displays.subprocess, 'run') as run, patch.object(displays, 'refresh_bar'):
            displays.apply(target)
        for call in run.call_args_list:
            args = call.args[0]
            self.assertEqual(args[args.index('--rate')+1], '144.00')

    def test_replaced_monitor_rejected_before_changes(self):
        before = self.row(1)
        before[0]['identity'] = 'new'
        target = copy.deepcopy(before)
        target[0]['identity'] = 'old'
        with patch.object(displays, 'query', return_value=before), patch.object(displays.subprocess, 'run') as run:
            with self.assertRaisesRegex(ValueError, 'cambiaron'):
                displays.apply(target)
        run.assert_not_called()

    def test_new_external_monitor_uses_highest_rate_instead_of_preferred_60(self):
        detected = self.row(1)
        detected[0].update(rate='60.00', rates={'1920x1080': ['143.85', '120.00', '60.00']})
        with patch.object(displays, 'load', return_value={}), patch.object(displays, 'query', return_value=copy.deepcopy(detected)), patch.object(displays, 'apply') as apply:
            displays.automatic(detected)
        self.assertEqual(apply.call_args.args[0][0]['rate'], '143.85')

    def test_saved_rate_is_respected_instead_of_forcing_maximum(self):
        detected = self.row(1)
        detected[0].update(rate='143.85', rates={'1920x1080': ['143.85', '60.00']})
        stored = copy.deepcopy(detected)
        stored[0]['rate'] = '60.00'
        with patch.object(displays, 'load', return_value={displays.key(detected): stored}), patch.object(displays, 'query', return_value=copy.deepcopy(detected)), patch.object(displays, 'apply') as apply:
            displays.automatic(detected)
        self.assertEqual(apply.call_args.args[0][0]['rate'], '60.00')

    def test_active_label_uses_running_rate_not_maximum_supported(self):
        screen = self.row(1)[0]
        screen.update(rate='60.00', rates={'1920x1080': ['143.85', '60.00']})
        self.assertEqual(displays.active_description(screen), 'Activo ahora: 1920x1080 · 60.00 Hz · aplicaciones 100 %')
        screen['enabled'] = False
        self.assertIn('apagada', displays.active_description(screen))

    def test_verification_rejects_requested_144_when_output_is_still_60(self):
        requested = self.row(1)
        requested[0]['rate'] = '143.85'
        actual = copy.deepcopy(requested)
        actual[0]['rate'] = '60.00'
        with self.assertRaisesRegex(ValueError, 'frecuencia'):
            displays.verify_applied(requested, actual)
        actual[0]['rate'] = '143.85'
        displays.verify_applied(requested, actual)

    def test_verification_rejects_a_resolution_fallback(self):
        requested = self.row(1)
        actual = copy.deepcopy(requested)
        actual[0]['mode'] = '1280x720'
        with self.assertRaisesRegex(ValueError, 'resolución'):
            displays.verify_applied(requested, actual)

    def test_application_scale_leaves_monitor_geometry_and_native_mode_unchanged(self):
        detected = self.row(2)
        old_size = displays.size(detected[0])
        detected[0].update(scale=125, rate='143.85', rates={'1920x1080': ['143.85', '60.00']})
        displays.reflow(detected, detected[0], old_size)
        self.assertEqual(displays.size(detected[0]), (1920, 1080))
        self.assertEqual(detected[1]['x'], 1920)
        displays.validate_layout(detected)
        args = displays.layout_args(detected)
        self.assertIn('1920x1080', args)
        self.assertIn('--transform', args)
        self.assertNotIn('--scale-from', args)
        self.assertIn('143.85', args)

    def test_application_scale_change_does_not_resize_or_rebuild_desktop(self):
        before = self.row(2)
        target = copy.deepcopy(before)
        target[0]['scale'] = 125
        with patch.object(displays, 'query', return_value=before), \
                patch.object(displays.subprocess, 'run') as run, \
                patch.object(displays, 'desktop_state') as state, \
                patch.object(displays, 'refresh_bar'):
            displays.apply(target)
        commands = [call.args[0] for call in run.call_args_list]
        self.assertEqual(len(commands), 2)
        self.assertIn('--dryrun', commands[0])
        self.assertIn('1920x1080', commands[1])
        self.assertNotIn('--fb', commands[1])
        self.assertNotIn('--scale-from', commands[1])
        state.assert_not_called()

    def test_verbose_query_separates_image_transform_from_saved_app_scale(self):
        listing = ('HDMI-0 connected 1536x864+0+0\n'
                   '    Transform: 0.800000 0.000000 0.000000\n'
                   '               0.000000 0.800000 0.000000\n'
                   '               0.000000 0.000000 1.000000\n'
                   '  1920x1080 (0x12) 325.00MHz +HSync *current\n'
                   '        h: width 1920 clock 162.0KHz\n'
                   '        v: height 1080 clock 143.85Hz\n')
        with patch.object(displays.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, listing)):
            screen = displays.query()[0]
        self.assertEqual(screen['mode'], '1920x1080')
        self.assertEqual(screen['rate'], '143.85')
        self.assertEqual(screen['transform_scale'], 125)
        self.assertEqual(screen['scale'], 100)
        self.assertEqual(displays.size(screen), (1920, 1080))

    def test_scale_at_pointer_selects_the_app_scale_for_that_monitor(self):
        detected = self.row(2)
        detected[0].update(x=0, scale=125)
        detected[1].update(x=1920, scale=150)
        with patch.object(displays, 'query', return_value=detected), \
                patch.object(displays.subprocess, 'run', return_value=subprocess.CompletedProcess(
                    [], 0, 'X=2000\nY=200\nSCREEN=0\nWINDOW=1\n')):
            self.assertEqual(displays.scale_at_pointer(), 1.5)

    def test_110_percent_has_a_visible_minimum_application_scale(self):
        detected = self.row(1)
        detected[0].update(x=0, scale=110)
        with patch.object(displays, 'query', return_value=detected), \
                patch.object(displays.subprocess, 'run', return_value=subprocess.CompletedProcess(
                    [], 0, 'X=200\nY=200\nSCREEN=0\nWINDOW=1\n')):
            self.assertEqual(displays.scale_at_pointer(), 1.2)

    def test_font_size_is_independent_per_monitor(self):
        detected = self.row(2)
        detected[0].update(x=0, font_size=12.5, polybar_scale=100)
        detected[1].update(x=1920, font_size=15, polybar_scale=90)
        with patch.object(displays, 'query', return_value=detected), \
                patch.object(displays.subprocess, 'run', return_value=subprocess.CompletedProcess(
                    [], 0, 'X=2000\nY=200\nSCREEN=0\nWINDOW=1\n')):
            self.assertEqual(displays.font_size_at_pointer(), 15)

    def test_scale_fallback_is_not_saved_as_success(self):
        requested = self.row(1)
        requested[0]['scale'] = 125
        actual = copy.deepcopy(requested)
        actual[0]['scale'] = 100
        with self.assertRaisesRegex(ValueError, 'escala'):
            displays.verify_applied(requested, actual)

    def test_appearance_is_saved_per_monitor_identity(self):
        detected = self.row(2)
        detected[0].update(identity='laptop', scale=100, font_size=12.5, polybar_scale=100)
        detected[1].update(identity='external', scale=125, font_size=15, polybar_scale=90)
        with tempfile.TemporaryDirectory() as directory, patch.object(displays, 'CONFIG', Path(directory) / 'displays.json'):
            displays.save(detected)
            settings = displays.read_json(Path(directory) / 'display-appearance.json')
        self.assertEqual(settings['laptop'], {'scale': 100, 'font_size': 12.5, 'polybar_scale': 100})
        self.assertEqual(settings['external'], {'scale': 125, 'font_size': 15, 'polybar_scale': 90})

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
        with patch.object(displays, 'query', return_value=detected), patch.object(displays.subprocess, 'run', side_effect=subprocess.CalledProcessError(1, 'xrandr')) as run:
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
