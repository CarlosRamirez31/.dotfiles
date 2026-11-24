import os
from pathlib import Path
import subprocess
import tempfile
import unittest


LOCK = Path(__file__).resolve().parents[2] / 'bin/dotfiles-lock'


class LockCache(unittest.TestCase):
    def test_monitor_changes_refresh_cache_without_locking_real_session(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            commands = home / 'bin'
            commands.mkdir()
            wallpaper = home / 'wallpaper.png'
            wallpaper.touch()
            (home / '.fehbg').write_text(f"feh --bg-fill '{wallpaper}'\n")
            monitors = home / 'monitors'
            monitors.write_text('Monitors: 1\n 0: DP-1 1920x1080+0+0\n')
            scripts = {
                'pgrep': 'exit 1',
                'bc': 'exit 0',
                'xdpyinfo': 'exit 0',
                'xrandr': 'cat "$HOME/monitors"',
                'betterlockscreen': '''
if [ "$1" = --update ]; then
    mkdir -p "$HOME/.cache/betterlockscreen/current"
    printf image > "$HOME/.cache/betterlockscreen/current/lock_dim.png"
    echo update >> "$HOME/updates"
fi
''',
            }
            for name, body in scripts.items():
                p = commands / name
                p.write_text('#!/bin/sh\n' + body + '\n')
                p.chmod(0o755)
            env = dict(os.environ, HOME=str(home), XDG_CACHE_HOME=str(home / '.cache'),
                       PATH=str(commands) + ':/usr/bin')
            for _ in range(2):
                subprocess.run(['bash', str(LOCK)], env=env, check=True)
            self.assertEqual((home / 'updates').read_text().splitlines(), ['update'])
            monitors.write_text('Monitors: 2\n 0: DP-1 1920x1080+0+0\n 1: HDMI-1 1920x1080+1920+0\n')
            subprocess.run(['bash', str(LOCK)], env=env, check=True)
            self.assertEqual((home / 'updates').read_text().splitlines(), ['update', 'update'])


if __name__ == '__main__':
    unittest.main()
