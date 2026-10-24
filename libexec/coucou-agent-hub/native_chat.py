"""Native CLI chat; no API keys, private session storage or model calls on discovery."""
import fcntl
import json
import os
from pathlib import Path
import subprocess
import tempfile
from agent_hub_terminal import BridgeError, atomic_json, private_dir, read_json, route_object


def send(bridge, request):
    agent = request.get('agent')
    if agent not in ('codex', 'hermes'):
        raise BridgeError('Elige Codex o Hermes.')
    query = request.get('query')
    if not isinstance(query, str) or not query.strip() or len(query) > 200000:
        raise BridgeError('Escribe un mensaje válido.')
    if request.get('context'):
        raise BridgeError('Los archivos adjuntos todavía requieren abrir la conversación en su terminal.')
    directory = private_dir(bridge.state / 'chat')
    path = directory / (agent + '.json')
    with open(directory / (agent + '.lock'), 'a+') as guard:
        os.fchmod(guard.fileno(), 0o600)
        try:
            fcntl.flock(guard, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise BridgeError('Este agente ya está respondiendo en Coucou.') from error
        item = read_json(path, {})
        if request.get('route'):
            route = route_object(request['route'])
            if route['agente'] != agent:
                raise BridgeError('La conversación pertenece a otro agente.')
            # An alias is resolved only by the exact route returned by the public CLI.
            matches = [c for c in bridge.hub('conversations', '--agent', agent, '--json')
                       if c.get('route') == route]
            if len(matches) != 1 or not matches[0].get('id'):
                raise BridgeError('La conversación seleccionada ya no está disponible.')
            _, cwd = bridge.validate(route)
            item = {'nativeId': matches[0]['id'], 'route': route, 'cwd': cwd}
        native = item.get('nativeId')
        if item.get('starting') and not native:
            raise BridgeError('El inicio anterior no devolvió un ID verificable. No se creará otra conversación automáticamente.')
        if native:
            route = item.get('route') or bridge.discover(agent, native)
            if not route:
                raise BridgeError('No se pudo verificar esta conversación en Agent Hub. No se abrió otra.')
            _, cwd = bridge.validate(route)
            metadata = read_json(bridge.metadata_path(agent, native), {})
            if metadata.get('active'):
                raise BridgeError('La sesión está activa. Detén o libera la ejecución desde su agente antes de continuar.')
            item['route'] = route
        else:
            # General Coucou chats have a neutral working directory, outside user repositories.
            cwd = str(private_dir(directory / 'general'))
        installed = [a for a in bridge.hub('agents', '--json') if a.get('id') == agent and a.get('installed')]
        if len(installed) != 1:
            raise BridgeError('El agente no está instalado o su adaptador es ambiguo.')
        adapter = installed[0]
        if agent == 'codex':
            argv = ['codex', 'exec']
            if native:
                argv += ['resume', native]
            argv += ['--json', '--skip-git-repo-check', '-']
        else:
            argv = ['hermes', 'chat', '--oneshot', '--format', 'stream-json', '--query-file', '-']
            if native:
                argv += ['--resume', native]
            if adapter.get('container'):
                argv = ['podman', 'exec', '-i', '--workdir', '/host-home' + cwd.removeprefix(str(Path.home())),
                        adapter['container'], '/usr/local/bin/hermes', *argv[1:]]
        item.update(cwd=cwd, starting=True)
        atomic_json(path, item)  # Unknown native identity must never cause an automatic duplicate.
        environment = dict(os.environ)
        for name in ('LD_PRELOAD', 'LD_LIBRARY_PATH', 'COUCOU_POLYBAR_CSS'):
            environment.pop(name, None)
        answer, failure = [], None
        # A tempfile avoids stderr backpressure and never persists credentials or prompts.
        with tempfile.TemporaryFile() as errors, tempfile.TemporaryFile() as prompt:
            prompt.write(query.encode('utf-8')); prompt.seek(0)
            try:
                process = bridge.spawn(argv, cwd=cwd, env=environment, stdin=prompt,
                                       stdout=subprocess.PIPE, stderr=errors, text=True, encoding='utf-8')
            except OSError as error:
                item['starting'] = False; atomic_json(path, item)
                raise BridgeError('No se pudo iniciar el agente: ' + str(error)) from error
            for line in process.stdout:
                try:
                    event = json.loads(line)
                except ValueError:
                    continue
                event_native = (event.get('thread_id') if event.get('type') == 'thread.started' else
                                event.get('session_id') if event.get('type') in ('system', 'result') else None)
                if event_native:
                    if item.get('nativeId') and event_native != item['nativeId']:
                        failure = 'El agente devolvió otra identidad de conversación.'
                        # Do not kill the agent or replace the selected identity.
                    else:
                        item['nativeId'] = event_native
                        atomic_json(path, item)
                if event.get('type') == 'item.completed' and event.get('item', {}).get('type') == 'agent_message':
                    answer.append(event['item'].get('text', ''))
                if event.get('type') == 'result':
                    answer = [event.get('text', '')]
                    if event.get('exit_code') or event.get('error'):
                        failure = event.get('error') or 'Hermes no pudo completar el turno.'
                if event.get('type') in ('error', 'turn.failed'):
                    failure = event.get('message') or str(event.get('error', 'El agente no completó el turno.'))
            code = process.wait()
            errors.seek(0)
            diagnostic = errors.read(4096).decode('utf-8', errors='replace')
        if item.get('nativeId'):
            item['starting'] = False
            try:
                if not item.get('route'):
                    item['route'] = bridge.discover(agent, item['nativeId'])
                if item.get('route'):
                    bridge.observe({'agent': agent, 'sessionId': item['nativeId'],
                                    'event': 'SessionStart', 'route': item['route']})
            except BridgeError:
                pass
            atomic_json(path, item)
        if failure or code:
            raise BridgeError(failure or diagnostic.strip() or 'El agente terminó con un error.')
        if not item.get('nativeId'):
            raise BridgeError('El agente no devolvió el ID nativo. No se creará otra sesión al reintentar.')
        if not answer or not ''.join(answer).strip():
            raise BridgeError('El agente terminó sin una respuesta de texto.')
        return {'ok': True, 'text': '\n\n'.join(answer), 'route': item.get('route'), 'nativeId': item['nativeId']}
