import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[2] / 'share/gpu-recovery/monitor.py'
spec = importlib.util.spec_from_file_location('recovery', SCRIPT)
recovery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recovery)


def sample(connected=False, ready=True, active=0, suspended=0, gpe=0):
    return dict(connected=connected, ready=ready, active=active, suspended=suspended, gpe=gpe)


class DetectorTest(unittest.TestCase):
    def test_disconnect_allows_grace_then_recovers_verified_cycle(self):
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

    def test_healthy_start_still_detects_later_cycle_without_replug(self):
        detector = recovery.Detector()
        detector.update(0, sample())
        detector.update(10, sample())
        self.assertFalse(detector.update(30, sample(suspended=20000)))
        self.assertFalse(detector.update(59, sample(suspended=49000)))
        detector.update(60, sample(suspended=50000))
        self.assertTrue(detector.update(80, sample(active=16000, suspended=54000, gpe=2)))

    def test_recurrence_after_recovery_gets_a_new_observation(self):
        detector = recovery.Detector()
        for now in (0, 10, 30, 89, 90, 109, 110):
            result = detector.update(now, sample(active=now * 800, suspended=now * 200,
                                                 gpe=now // 10))
            self.assertEqual(result, now in (30, 110))

    def test_hourly_budget_survives_replug_and_expires(self):
        detector = recovery.Detector()

        def cycle(now, connected=False):
            return detector.update(now, sample(connected=connected, active=now * 800,
                                               suspended=now * 200, gpe=now // 10))

        for now in (0, 10, 30, 90, 110, 170, 190):
            self.assertEqual(cycle(now), now in (30, 110, 190))
        self.assertFalse(cycle(191, connected=True))
        self.assertFalse(cycle(192))
        for now in (250, 270, 3600, 3629):
            self.assertFalse(cycle(now))
            self.assertIsNone(detector.baseline)
        self.assertFalse(cycle(3630))
        self.assertTrue(cycle(3650))
        self.assertEqual(list(detector.attempts), [110, 190, 3650])

    def test_enabled_output_discards_partial_observation(self):
        detector = recovery.Detector()
        detector.update(0, sample())
        detector.update(10, sample())
        detector.update(20, sample(ready=False, active=16000, suspended=4000, gpe=2))
        self.assertIsNone(detector.baseline)
        self.assertFalse(detector.update(40, sample(active=32000, suspended=8000, gpe=4)))
        self.assertTrue(detector.update(60, sample(active=48000, suspended=12000, gpe=6)))

    def test_counter_reset_requires_a_fresh_window(self):
        detector = recovery.Detector()
        detector.update(0, sample(active=100000, suspended=10000, gpe=20))
        detector.update(10, sample(active=100000, suspended=10000, gpe=20))
        self.assertFalse(detector.update(30, sample()))
        self.assertTrue(detector.update(50, sample(active=16000, suspended=4000, gpe=2)))


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
