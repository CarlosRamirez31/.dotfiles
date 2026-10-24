"""Keep Xephyr's output in sync when a small desktop is enlarged."""
from pathlib import Path
import runpy
import subprocess
import unittest
from unittest.mock import MagicMock, patch

SCRIPT = Path(__file__).resolve().parents[2] / 'environments/hermes/payload/bin/resize-watch'


class PresentationResizeTests(unittest.TestCase):
    def run_watcher(self, sizes, refresh_codes=()):
        sizes = iter(sizes)
        codes = iter(refresh_codes)
        event = MagicMock()
        event.is_set.side_effect = [False, False, True]
        path = MagicMock()
        path.__truediv__.return_value = path
        path.read_text.return_value = ''
        path.is_file.return_value = False
        calls = []

        def run(args, **kwargs):
            calls.append(args)
            if args == ['xdpyinfo']:
                return subprocess.CompletedProcess(args, 0, f'dimensions: {next(sizes)} pixels')
            if args == ['xrandr', '--query']:
                return subprocess.CompletedProcess(args, next(codes, 0))
            return subprocess.CompletedProcess(args, 0)

        with patch('threading.Event', return_value=event), \
             patch('signal.signal'), patch('pathlib.Path', return_value=path), \
             patch('subprocess.run', side_effect=run), patch('subprocess.Popen'):
            runpy.run_path(str(SCRIPT))
        return calls

    def test_each_resize_polls_output_before_publishing_new_monitor(self):
        calls = self.run_watcher(['941x1007', '1896x1007'])
        for width in (941, 1896):
            monitor = next(i for i, c in enumerate(calls)
                           if c[:3] == ['xrandr', '--setmonitor', 'Virtual']
                           and c[3].startswith(f'{width}/'))
            self.assertEqual(calls[monitor - 2], ['xrandr', '--query'])
            self.assertEqual(calls[monitor - 1], ['xrandr', '--delmonitor', 'Virtual'])

    def test_failed_refresh_retries_without_publishing_stale_geometry(self):
        calls = self.run_watcher(['1896x1007', '1896x1007'], [1, 0])
        self.assertEqual(calls.count(['xrandr', '--query']), 2)
        self.assertEqual(sum(c[:2] == ['xrandr', '--setmonitor'] for c in calls), 1)


if __name__ == '__main__':
    unittest.main()
