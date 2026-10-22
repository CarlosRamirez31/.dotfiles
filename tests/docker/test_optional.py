import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[2]
LIB = REPO / 'libexec/dotfiles-container-env'


class ContainerSetup(unittest.TestCase):
    def selected(self, *args):
        output = subprocess.check_output([str(REPO / 'install.sh'), '--dry-run', *args], text=True)
        return output.strip().split(': ', 1)[1].split()

    def test_optional_apps_are_explicit_only(self):
        default = self.selected()
        self.assertEqual(default, self.selected('all'))
        for name in ('docker', 'dbeaver'):
            self.assertNotIn(name, default)
            self.assertEqual([name], self.selected(name))
            self.assertEqual(default + [name], self.selected('all', name))
            result = subprocess.run(
                ['bash', str(REPO / 'setup/modules' / name / 'setup-container.sh')],
                env=dict(os.environ, CONTAINER_ID=''), capture_output=True, text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('el contenedor dev', result.stderr)

    def test_endpoint_selection_respects_user_settings(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'podman').mkdir()
            (root / 'config').mkdir()
            endpoint = root / 'podman/podman.sock'
            with socket.socket(socket.AF_UNIX) as server:
                server.bind(str(endpoint))
                env = dict(os.environ, XDG_RUNTIME_DIR=str(root), DOCKER_CONFIG=str(root / 'config'))
                env.pop('DOCKER_HOST', None)
                env.pop('DOCKER_CONTEXT', None)
                def run(*args, **overrides):
                    output = subprocess.check_output(
                        ['bash', '-c', 'source "$1"; shift; dotfiles_container_env "$@"; printf "%s|%s" "${DOCKER_HOST:-}" "${DOCKER_CONTEXT:-}"',
                         'test', str(LIB), *args], env=dict(env, **overrides), text=True,
                    )
                    return output
                self.assertEqual(run(), 'unix://' + str(endpoint) + '|')
                self.assertEqual(run(DOCKER_HOST='tcp://example:2376'), 'tcp://example:2376|')
                self.assertEqual(run(DOCKER_CONTEXT='custom'), '|custom')
                self.assertEqual(run('--context', 'custom', 'ps'), '|')
                self.assertEqual(run('-H', 'ssh://remote', 'ps'), '|')
                self.assertEqual(run('run', '--rm', 'image', 'sh', '-c', 'echo ok'), 'unix://' + str(endpoint) + '|')
                (root / 'config/config.json').write_text(json.dumps({'currentContext': 'custom'}))
                self.assertEqual(run(), '|')


if __name__ == '__main__':
    unittest.main()
