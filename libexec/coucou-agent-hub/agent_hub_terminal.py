#!/usr/bin/env python3
"""Coucou's local terminal bridge. Agent Hub is accessed exclusively through CLI JSON."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import uuid

if __name__ == '__main__':
    sys.modules.setdefault('agent_hub_terminal', sys.modules[__name__])


class BridgeError(Exception):
    pass


def route_object(value):
    if not isinstance(value, dict) or type(value.get('version')) is not int or value['version'] != 1:
        raise BridgeError('Descriptor de conversación no válido (version debe ser 1).')
    for field in ('idCarpeta', 'idMessage', 'agente'):
        if not isinstance(value.get(field), str) or not value[field] or '\0' in value[field]:
            raise BridgeError('Descriptor no válido: ' + field)
    return value  # Preserve the complete descriptor, including opaque IDs and additional fields.


def key(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def private_dir(path):
    path = Path(path).absolute()
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    if path.is_symlink() or path.stat().st_uid != os.getuid():
        raise BridgeError('El directorio de estado no pertenece al usuario o es un enlace.')
    path.chmod(0o700)
    return path


def atomic_json(path, value):
    fd, temporary = tempfile.mkstemp(prefix='.pending-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as output:
            os.fchmod(output.fileno(), 0o600)
            json.dump(value, output, ensure_ascii=False)
            output.write('\n')
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def read_json(path, default=None):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError:
        return default


class HubTerminal:
    def __init__(self, state=None, config=None, run=subprocess.run, spawn=subprocess.Popen, which=shutil.which):
        home = Path.home()
        self.state = private_dir(state or home / '.local/share/coucou/agent-hub')
        self.executions = private_dir(self.state / 'executions')
        self.routes = private_dir(self.state / 'routes')
        self.locks = private_dir(self.state / 'locks')
        self.config = config if config is not None else read_json(
            Path(os.environ.get('XDG_CONFIG_HOME', home / '.config')) / 'coucou/agent-hub.json', {})
        self.run, self.spawn, self.which = run, spawn, which

    def hub(self, *args):
        if not self.which('agent-hub'):
            raise BridgeError('No se encuentra agent-hub en PATH. No se abrió ninguna conversación.')
        try:
            result = self.run(['agent-hub', *args], capture_output=True, text=True,
                              encoding='utf-8', timeout=20, check=False)
        except (OSError, subprocess.TimeoutExpired) as error:
            raise BridgeError('No se pudo consultar Agent Hub: ' + str(error)) from error
        if result.returncode:
            raise BridgeError(result.stderr.strip()[:4000] or 'Agent Hub rechazó la operación.')
        try:
            return json.loads(result.stdout)
        except ValueError as error:
            raise BridgeError('Agent Hub devolvió una respuesta JSON no válida.') from error

    def metadata_path(self, agent, session):
        if not isinstance(agent, str) or not agent or not isinstance(session, str) or not session:
            raise BridgeError('Falta la identidad de la ejecución seleccionada.')
        return self.executions / (key([agent, session]) + '.json')

    def discover(self, agent, session):
        # Exact native ID or stable alias only. Never compare cwd, title, time or list order.
        matches = [item['route'] for item in self.hub('conversations', '--agent', agent, '--json')
                   if item.get('id') == session or item.get('route', {}).get('idMessage') == session]
        if len(matches) != 1:
            return None
        route = route_object(matches[0])
        if route['agente'] != agent:
            raise BridgeError('Agent Hub devolvió un adaptador distinto del de la ejecución.')
        return route

    def observe(self, request):
        agent, session = request.get('agent'), request.get('sessionId')
        path = self.metadata_path(agent, session)
        lock = self.locks / (path.stem + '-metadata.lock')
        with open(lock, 'a+', encoding='utf-8') as output:
            os.chmod(lock, 0o600)
            fcntl.flock(output, fcntl.LOCK_EX)
            item = read_json(path, {'agent': agent, 'sessionId': session})
            event = request.get('event')
            if event in ('UserPromptSubmit', 'PreToolUse', 'PermissionRequest'):
                item['active'] = True
            elif event in ('Stop', 'Interrupt', 'SessionEnd'):
                item['active'] = False
            supplied = request.get('route')
            if supplied is not None:
                supplied = route_object(supplied)
                if supplied['agente'] != agent:
                    raise BridgeError('El descriptor no corresponde al agente de esta ejecución.')
                # The runner explicitly supplied a descriptor for this exact execution.
                item['route'] = supplied
            elif not item.get('route'):
                try:
                    item['route'] = self.discover(agent, session)
                except BridgeError:
                    # Missing hub or an unindexed session never interferes with the runner.
                    item['route'] = None
            atomic_json(path, item)
        return {'ok': True, 'metadata': item}

    def selected(self, request):
        session, agent = request.get('sessionId'), request.get('agent')
        if request.get('route') is not None:
            route = route_object(request['route'])
            if agent and route['agente'] != agent:
                raise BridgeError('El descriptor y la ejecución pertenecen a agentes distintos.')
            return route
        if agent and session:
            path = self.metadata_path(agent, session)
            item = read_json(path)
            if item and item.get('route'):
                return route_object(item['route'])
            route = self.discover(agent, session)
            if route:
                self.associate(dict(request, route=route))
            return route
        if session:
            matches = [item for path in self.executions.glob('*.json')
                       if (item := read_json(path, {})).get('sessionId') == session and item.get('route')]
            if len(matches) == 1:
                return route_object(matches[0]['route'])
        return None  # Legacy task: explicit selection, never resume --all or another agent.

    def associate(self, request):
        route = route_object(request.get('route'))
        agent, session = request.get('agent'), request.get('sessionId')
        if agent and route['agente'] != agent:
            raise BridgeError('Selecciona una conversación del agente que ejecutó esta tarea.')
        # Validate selected conversations before storing them. No automatic creation on failure.
        self.validate(route)
        if session:
            path = self.metadata_path(agent or route['agente'], session)
            lock = self.locks / (path.stem + '-metadata.lock')
            with open(lock, 'a+', encoding='utf-8') as output:
                os.chmod(lock, 0o600)
                fcntl.flock(output, fcntl.LOCK_EX)
                item = read_json(path, {'agent': agent or route['agente'], 'sessionId': session})
                item['route'] = route
                atomic_json(path, item)
        return {'ok': True, 'route': route}

    def validate(self, route):
        route_object(route)
        path = self.routes / (uuid.uuid4().hex + '.json')
        atomic_json(path, route)
        result = self.hub('open', '--route-file', str(path), '--dry-run')
        if result.get('valid') is not True or result.get('route') != route:
            raise BridgeError('Agent Hub no validó exactamente el descriptor seleccionado.')
        cwd = result.get('cwd')
        if not isinstance(cwd, str) or not Path(cwd).is_absolute() or not Path(cwd).is_dir():
            raise BridgeError('La carpeta validada no existe o no es una ruta absoluta.')
        return path, cwd

    def terminal_argv(self, child, cwd):
        terminal = self.config.get('terminal', {})
        program = terminal.get('program')
        adapter = terminal.get('adapter')
        extra = terminal.get('args', [])
        if not isinstance(program, str) or not self.which(program):
            raise BridgeError('Configura el emulador en Coucou: agent-hub.json → terminal.')
        if not isinstance(extra, list) or not all(isinstance(a, str) and '\0' not in a for a in extra):
            raise BridgeError('Los argumentos del emulador deben ser una lista de cadenas.')
        options = {
            'alacritty': ['--working-directory', cwd, '-e'],
            'kitty': ['--directory', cwd, '--'],
            'gnome-terminal': ['--wait', '--working-directory', cwd, '--'],
            'konsole': ['--nofork', '--workdir', cwd, '-e'],
            'wezterm': ['start', '--always-new-process', '--cwd', cwd, '--'],
            'foot': ['--working-directory=' + cwd, '--'],
            'xterm': ['-e'],
            'xfce4-terminal': ['--disable-server', '--working-directory', cwd, '--execute'],
        }
        if adapter not in options:
            raise BridgeError('Adaptador de terminal no admitido; no se ejecutó ningún comando.')
        return [program, *extra, *options[adapter], *child]

    @staticmethod
    def process_token(pid):
        try:
            # Process identity only, never agent credentials, SQLite or private session files.
            return Path(f'/proc/{int(pid)}/stat').read_text().rsplit(')', 1)[1].split()[19]
        except (OSError, ValueError, IndexError):
            return None

    def open(self, request):
        route = self.selected(request)
        if route is None:
            if request.get('autoCreate') and request.get('agent'):
                route = self.new_general(request)['route']
            else:
                return {'ok': False, 'needsAssociation': True}
        agent, session = request.get('agent') or route['agente'], request.get('sessionId')
        if session:
            item = read_json(self.metadata_path(agent, session), {})
            if item.get('active'):
                raise BridgeError('Esta ejecución sigue activa o esperando permiso en Coucou. '
                                  'Detén o libera la ejecución desde su agente antes de reintentar; no se forzó ningún bloqueo.')
        identity = key([route['agente'], route['idCarpeta'], route['idMessage']])
        guard = self.locks / (identity + '.lock')
        with open(guard, 'a+', encoding='utf-8') as output:
            os.chmod(guard, 0o600)
            try:
                fcntl.flock(output, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise BridgeError('Esta conversación ya se está abriendo.') from error
            lease = read_json(self.locks / (identity + '.json'), {})
            if lease and (time.time() - lease.get('time', 0) < 2 or
                          (lease.get('token') and self.process_token(lease['pid']) == lease['token'])):
                raise BridgeError('Esta conversación ya está abierta o se está abriendo en una terminal.')
            path, cwd = self.validate(route)
            child = ['agent-hub', 'open', '--route-file', str(path)]
            if self.config.get('returnToAgents') is True:
                lifecycle = Path(__file__).resolve().with_name('terminal_session.py')
                if not lifecycle.is_file():
                    raise BridgeError('Falta el controlador de salida de Coucou; no se abrió la terminal.')
                terminal_child = [sys.executable, str(lifecycle), '--route-file', str(path)]
            else:
                terminal_child = child
            argv = self.terminal_argv(terminal_child, cwd)
            environment = dict(os.environ)
            for name in ('LD_PRELOAD', 'LD_LIBRARY_PATH', 'COUCOU_POLYBAR_CSS'):
                environment.pop(name, None)
            try:
                process = self.spawn(argv, cwd=cwd, env=environment, start_new_session=True,
                                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except OSError as error:
                raise BridgeError('No se pudo abrir el emulador: ' + str(error)) from error
            atomic_json(self.locks / (identity + '.json'),
                        {'pid': process.pid, 'token': self.process_token(process.pid), 'time': time.time()})
        return {'ok': True, 'route': route, 'routeFile': str(path)}

    def new_general(self, request):
        agent, session = request.get('agent'), request.get('sessionId')
        if not agent or not session:
            raise BridgeError('No se pudo identificar el agente de esta ejecución.')
        path = self.metadata_path(agent, session)
        guard = self.locks / (path.stem + '-metadata.lock')
        with open(guard, 'a+') as output:
            os.fchmod(output.fileno(), 0o600)
            fcntl.flock(output, fcntl.LOCK_EX)
            item = read_json(path, {'agent': agent, 'sessionId': session})
            if item.get('active'):
                raise BridgeError('Esta ejecución está activa; detén o libera su agente antes de continuar.')
            if item.get('route'):
                return {'ok': True, 'route': route_object(item['route'])}
            if item.get('creating'):
                raise BridgeError('El inicio anterior no pudo confirmarse. No se creará un duplicado.')
            projects = self.hub('projects', '--agent', agent, '--json')
            matches = [p for p in projects if p.get('roots') == [str(Path.home())]]
            if len(matches) != 1:
                raise BridgeError('Agent Hub no ofrece una ubicación general única para este agente.')
            folder = matches[0].get('idCarpeta') or matches[0]['id']
            item['creating'] = True
            atomic_json(path, item)
            route = route_object(self.hub('new', '--agent', agent, '--folder', folder, '--json'))
            if route['agente'] != agent or route['idCarpeta'] != folder:
                raise BridgeError('Agent Hub devolvió otro agente o ubicación.')
            item.update(route=route, creating=False)
            atomic_json(path, item)
            return {'ok': True, 'route': route}

    def handle(self, request):
        action = request.get('action')
        if action == 'chat-reset':
            agent = request.get('agent')
            if agent not in ('codex', 'hermes'):
                raise BridgeError('Agente de chat no válido.')
            directory = private_dir(self.state / 'chat')
            with open(directory / (agent + '.lock'), 'a+') as guard:
                os.fchmod(guard.fileno(), 0o600)
                try:
                    fcntl.flock(guard, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError as error:
                    raise BridgeError('El agente todavía está respondiendo.') from error
                path = directory / (agent + '.json')
                if path.exists():
                    archive = private_dir(directory / 'archive')
                    os.replace(path, archive / (agent + '-' + uuid.uuid4().hex + '.json'))
            return {'ok': True}
        if action == 'chat':
            from native_chat import send
            return send(self, request)
        if action == 'observe':
            return self.observe(request)
        if action == 'open':
            return self.open(request)
        if action == 'associate':
            return self.associate(request)
        if action == 'agents':
            return {'ok': True, 'items': self.hub('agents', '--json')}
        if action in ('conversations', 'projects'):
            agent = request.get('agent')
            if not isinstance(agent, str) or not agent:
                raise BridgeError('Selecciona el agente de esta ejecución.')
            return {'ok': True, 'items': self.hub(action, '--agent', agent, '--json')}
        if action == 'new':
            if request.get('confirmed') is not True:
                raise BridgeError('Crear una conversación nueva requiere una elección explícita.')
            agent, folder = request.get('agent'), request.get('folder')
            if not isinstance(agent, str) or not agent or not isinstance(folder, str) or not folder:
                raise BridgeError('Falta el agente o el ID real del proyecto.')
            route = route_object(self.hub('new', '--agent', agent, '--folder', folder, '--json'))
            if route['agente'] != agent or route['idCarpeta'] != folder:
                raise BridgeError('Agent Hub devolvió un descriptor para otro agente o proyecto.')
            # Persist the stable descriptor BEFORE any attempt to launch it.
            atomic_json(self.executions / ('created-' + key(route) + '.json'), {'route': route})
            return self.associate(dict(request, route=route))
        raise BridgeError('Operación de terminal desconocida.')


def main():
    try:
        request = json.load(sys.stdin)
        response = HubTerminal().handle(request)
    except (BridgeError, OSError, ValueError, TypeError, KeyError) as error:
        response = {'ok': False, 'error': str(error)}
    json.dump(response, sys.stdout, ensure_ascii=False)
    sys.stdout.write('\n')


if __name__ == '__main__':
    main()
