import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch


PLUGIN = Path(__file__).parents[2] / 'share/coucou/hermes-plugin/__init__.py'
SPEC = importlib.util.spec_from_file_location('coucou_hermes_plugin', PLUGIN)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class Request:
    request_id = 'bound-request-1'
    command = 'printf safe'
    description = 'test command'
    timeout_seconds = 1
    allowed_choices = ('once', 'deny')


class ApprovalTransportTests(unittest.TestCase):
    def exchange(self, reply):
        class FakeSocket:
            def __init__(self):
                self.sent = bytearray()
                self.parts = iter([bytes([byte]) for byte in (reply or b'')])

            def __enter__(self): return self
            def __exit__(self, *_): return False
            def settimeout(self, value): self.timeout = value
            def connect(self, path): self.path = path
            def sendall(self, data): self.sent.extend(data)
            def recv(self, size): return next(self.parts, b'')

        fake = FakeSocket()
        with patch.object(MODULE.socket, 'socket', return_value=fake):
            result = MODULE._approval_decision(Request(), '/test/event.sock')
        header, payload = bytes(fake.sent).split(b'\n', 1)
        self.assertEqual(header, b'COUCOU_APPROVAL')
        return result, json.loads(payload)

    def test_allow_is_a_bound_one_shot_decision(self):
        result, event = self.exchange(b'allow\n')
        self.assertEqual(result, 'once')
        self.assertEqual(event['hook_event_name'], 'PermissionRequest')
        self.assertEqual(event['coucou_agent'], 'hermes')
        self.assertEqual(event['session_id'], Request.request_id)
        self.assertEqual(event['tool_input']['command'], Request.command)

    def test_every_non_allow_response_fails_closed(self):
        for reply in (b'deny\n', b'always\n', b'garbage\n', None):
            with self.subTest(reply=reply):
                result, _ = self.exchange(reply)
                self.assertEqual(result, 'deny')

    def test_transport_refuses_requests_without_once_scope(self):
        request = Request()
        request.allowed_choices = ('session', 'deny')
        self.assertEqual(MODULE._approval_decision(request, '/missing/socket'), 'deny')

    def test_unavailable_transport_fails_closed(self):
        with patch.object(MODULE.socket, 'socket', side_effect=OSError('unavailable')):
            self.assertEqual(MODULE._approval_decision(Request(), '/missing/socket'), 'deny')


if __name__ == '__main__':
    unittest.main()
