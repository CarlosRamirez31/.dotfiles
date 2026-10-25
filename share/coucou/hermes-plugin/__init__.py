"""Local Coucou event observer and request-bound Hermes approval transport."""
import json
import os
import queue
import socket
import threading

SOCKET = '/host-home/.local/share/coucou/hermes-bridge/event.sock'
MAX_APPROVAL_BYTES = 65536
APPROVAL_TIMEOUT = 105.0
_queue = queue.Queue(maxsize=128)
_started = False
_start_lock = threading.Lock()


def _worker():
    while True:
        payload = _queue.get()
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as stream:
                stream.settimeout(.25)
                stream.connect(SOCKET)
                stream.sendall(json.dumps(payload, ensure_ascii=False).encode('utf-8') + b'\n')
        except (OSError, ValueError):
            pass  # Coucou closed/unreachable: Hermes continues normally.
        finally:
            _queue.task_done()


def _enqueue(payload):
    global _started
    with _start_lock:
        if not _started:
            threading.Thread(target=_worker, name='coucou-observer', daemon=True).start()
            _started = True
    try:
        _queue.put_nowait(payload)
    except queue.Full:
        pass


def _approval_decision(request, socket_path=SOCKET):
    """Return only an explicit one-shot human decision; every error denies."""
    if 'once' not in getattr(request, 'allowed_choices', ()):
        return 'deny'
    try:
        timeout = min(max(float(request.timeout_seconds), 0.1), APPROVAL_TIMEOUT)
        command = request.command if isinstance(request.command, str) else ''
        description = request.description if isinstance(request.description, str) else ''
        payload = {
            'coucou_agent': 'hermes', 'hook_event_name': 'PermissionRequest',
            'session_id': request.request_id, 'cwd': os.getcwd(), 'tool_name': 'Terminal',
            'tool_input': {'command': command, 'description': description},
        }
        encoded = json.dumps(payload, ensure_ascii=False).encode('utf-8') + b'\n'
        if len(encoded) > MAX_APPROVAL_BYTES:
            return 'deny'
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as stream:
            stream.settimeout(timeout)
            stream.connect(socket_path)
            stream.sendall(b'COUCOU_APPROVAL\n' + encoded)
            response = bytearray()
            while len(response) <= 16:
                part = stream.recv(1)
                if not part or part == b'\n':
                    break
                response.extend(part)
        return 'once' if bytes(response) == b'allow' else 'deny'
    except (OSError, TypeError, ValueError, OverflowError):
        return 'deny'


def register(ctx):
    task_sessions = {}
    lock = threading.Lock()

    def emit(event, session, **fields):
        if not isinstance(session, str) or not session:
            return
        cwd = os.getcwd()
        if cwd == '/host-home' or cwd.startswith('/host-home/'):
            cwd = '/home/beambollow' + cwd[len('/host-home'):]
        _enqueue({'coucou_agent': 'hermes', 'hook_event_name': event,
                  'session_id': session, 'cwd': cwd, **fields})

    def session_start(**kwargs):
        emit('SessionStart', kwargs.get('session_id'))

    def before_turn(**kwargs):
        emit('UserPromptSubmit', kwargs.get('session_id'))

    def after_turn(**kwargs):
        emit('Stop', kwargs.get('session_id'))

    def api_request(**kwargs):
        # Both correlation fields come from Hermes' documented API-request hook.
        task, session = kwargs.get('task_id'), kwargs.get('session_id')
        if isinstance(task, str) and task and isinstance(session, str) and session:
            with lock:
                task_sessions[task] = session

    def tool_session(kwargs):
        if kwargs.get('session_id'):
            return kwargs['session_id']
        with lock:
            return task_sessions.get(kwargs.get('task_id'))

    def before_tool(**kwargs):
        emit('PreToolUse', tool_session(kwargs), tool_name=kwargs.get('tool_name', ''),
             tool_input=kwargs.get('args') or {})

    def after_tool(**kwargs):
        emit('PostToolUse', tool_session(kwargs), tool_name=kwargs.get('tool_name', ''))

    def session_end(**kwargs):
        session = kwargs.get('session_id')
        emit('Interrupt' if kwargs.get('interrupted') else 'SessionEnd', session)
        with lock:
            for task in [task for task, sid in task_sessions.items() if sid == session]:
                del task_sessions[task]

    ctx.register_approval_transport('coucou', _approval_decision)

    for name, callback in [('on_session_start', session_start), ('pre_llm_call', before_turn),
                           ('post_llm_call', after_turn), ('pre_api_request', api_request),
                           ('pre_tool_call', before_tool), ('post_tool_call', after_tool),
                           ('on_session_end', session_end)]:
        ctx.register_hook(name, callback)
