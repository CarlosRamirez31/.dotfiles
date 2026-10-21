import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'dotfiles/.local/share/gpu-recovery/monitor.py'
spec = importlib.util.spec_from_file_location('recovery', SCRIPT)
recovery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recovery)


def sample(connected=False, ready=True, active=0, suspended=0, gpe=0):
    return dict(connected=connected, ready=ready, active=active, suspended=suspended, gpe=gpe)


class DetectorTest(unittest.TestCase):
    def test_disconnect_allows_grace_then_recovers_one_verified_cycle(self):
        detector = recovery.Detector()
        self.assertFalse(detector.update(0, sample(connected=True)))
        self.assertFalse(detector.update(1, sample()))
        self.assertFalse(detector.update(10, sample()))
        self.assertFalse(detector.update(11, sample()))
        self.assertTrue(detector.update(31, sample(active=16000, suspended=4000, gpe=2)))
        self.assertFalse(detector.update(100, sample(active=80000, suspended=8000, gpe=12)))

    def test_healthy_gpu_and_busy_gpu_without_gpe_cycle_are_left_alone(self):
        for end in (sample(suspended=20000), sample(active=20000, gpe=4),
                    sample(active=19000, suspended=1000, gpe=1)):
            detector = recovery.Detector()
            detector.update(0, sample())
            detector.update(10, sample())
            self.assertFalse(detector.update(30, end))

    def test_reconnect_cancels_pending_assessment(self):
        detector = recovery.Detector()
        detector.update(0, sample())
        detector.update(10, sample())
        self.assertFalse(detector.update(20, sample(connected=True)))
        self.assertFalse(detector.update(40, sample(connected=True, active=16000, suspended=4000, gpe=2)))

    def test_waits_for_stale_outputs_to_be_disabled(self):
        detector = recovery.Detector()
        detector.update(0, sample(ready=False))
        detector.update(40, sample(ready=False))
        self.assertIsNone(detector.baseline)
        detector.update(41, sample())
        self.assertTrue(detector.update(61, sample(active=16000, suspended=4000, gpe=2)))

    def test_quick_replug_cannot_bypass_cooldown(self):
        detector = recovery.Detector()
        detector.update(0, sample())
        detector.update(10, sample())
        self.assertTrue(detector.update(30, sample(active=16000, suspended=4000, gpe=2)))
        detector.update(31, sample(connected=True))
        detector.update(32, sample())
        detector.update(89, sample())
        self.assertIsNone(detector.baseline)
        detector.update(90, sample())
        self.assertTrue(detector.update(110, sample(active=16000, suspended=4000, gpe=2)))


class Event:
    def __init__(self):
        self.enabled = True
        self.commands = []

    def read_text(self):
        return '10 ' + ('enabled' if self.enabled else 'disabled') + ' unmasked'

    def write_text(self, value):
        if value not in ('enable\n', 'disable\n'):
            raise OSError(22, 'Invalid argument')
        self.commands.append(value)
        self.enabled = value == 'enable\n'


class RestoreTest(unittest.TestCase):
    def test_normal_interrupt_and_failure_restore_event_and_remove_marker(self):
        for failure in (None, KeyboardInterrupt, OSError):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                hardware = recovery.Hardware(root=root, runtime=root / 'runtime')
                hardware.gpe = Event()
                (hardware.gpu / 'power').mkdir(parents=True)
                (hardware.gpu / 'power/runtime_status').write_text('suspended')

                def sleep(seconds):
                    if failure:
                        raise failure

                with patch.object(hardware, 'connectors', return_value=(False, False)):
                    if failure:
                        with self.assertRaises(failure):
                            hardware.recover(sleep=sleep)
                    else:
                        hardware.recover(sleep=sleep)
                self.assertTrue(hardware.gpe.enabled)
                self.assertEqual(hardware.gpe.commands, ['disable\n', 'enable\n'])
                self.assertFalse(hardware.marker.exists())

    def test_restore_marker_handles_forced_termination(self):
        with tempfile.TemporaryDirectory() as directory:
            hardware = recovery.Hardware(runtime=Path(directory))
            hardware.gpe = Event()
            hardware.gpe.enabled = False
            hardware.marker.write_text('restore enable\n')
            hardware.restore()
            self.assertTrue(hardware.gpe.enabled)
            self.assertFalse(hardware.marker.exists())

    def test_connected_monitor_prevents_recovery(self):
        hardware = recovery.Hardware()
        hardware.gpe = Event()
        with patch.object(hardware, 'connectors', return_value=(True, True)):
            hardware.recover()
        self.assertEqual(hardware.gpe.commands, [])


if __name__ == '__main__':
    unittest.main()
