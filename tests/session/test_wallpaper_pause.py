import fcntl
import json
import os
from pathlib import Path
import runpy
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

HELPER = Path(__file__).resolve().parents[2] / 'bin/dotfiles-wallpaper-pause'

class WallpaperPauseTests(unittest.TestCase):
    def test_per_screen_picker_readiness_and_pid_identity(self):
        players = [subprocess.Popen(['sleep', '30'], start_new_session=True) for _ in range(2)]
        try:
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                cache = root / 'cache/wallpaper_picker'
                cache.mkdir(parents=True)
                ready = root / 'ready'
                ready.touch()
                records = []
                for index, p in enumerate(players):
                    fields = (Path('/proc') / str(p.pid) / 'stat').read_text().rsplit(')', 1)[1].split()
                    records.append(dict(pid=p.pid, start=fields[19], bounds=[index*1920, 0, 1920, 1080], ready=str(ready)))
                registry = root / 'dotfiles-wallpaper-players.json'
                def save():
                    registry.write_text(json.dumps(dict(controller=os.getpid(), players=records)))
                def execute(*args):
                    with patch.dict(os.environ, XDG_RUNTIME_DIR=str(root), XDG_CACHE_HOME=str(root/'cache')), \
                         patch.object(sys, 'argv', [str(HELPER), *args]), \
                         patch('subprocess.check_output', return_value=str(os.getpid())):
                        runpy.run_path(str(HELPER), run_name='__main__')
                    time.sleep(.02)
                def stopped(p):
                    return (Path('/proc') / str(p.pid) / 'stat').read_text().rsplit(')', 1)[1].split()[0] == 'T'
                save()
                execute('screens', '1920,0,1920,1080')
                self.assertFalse(stopped(players[0]))
                self.assertTrue(stopped(players[1]))
                with (cache/'picker.lock').open('a') as lock:
                    fcntl.flock(lock, fcntl.LOCK_EX)
                    execute('refresh')
                    self.assertTrue(all(stopped(p) for p in players))
                execute('refresh')
                self.assertFalse(stopped(players[0]))
                self.assertTrue(stopped(players[1]))
                # Scene players pause rendering cooperatively, never SIGSTOP GLX.
                pause_file = root / 'scene.pause'
                records[1]['pause_file'] = str(pause_file)
                save()
                execute('refresh')
                self.assertTrue(pause_file.exists())
                self.assertFalse(stopped(players[1]))
                ready.unlink()
                execute('refresh')
                self.assertFalse(any(stopped(p) for p in players))
                self.assertFalse(pause_file.exists())
                ready.touch()
                records[1]['start'] = 'invalid'
                save()
                execute('refresh')
                self.assertFalse(stopped(players[1]))
        finally:
            for p in players:
                os.killpg(p.pid, signal.SIGCONT)
                p.terminate()
                p.wait()
