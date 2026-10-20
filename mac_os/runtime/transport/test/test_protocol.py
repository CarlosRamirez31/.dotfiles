import io
import json
import struct
import unittest

from ports.result import ErrorCode, Failure, Success
from ports.worker_mode import WorkerMode
from transport.personal_voice import serve


class Adapter:
    def __init__(self, result):
        self.result = result
        self.calls = 0

    def set_embedding(self, pcm):
        return Success(None)

    def enroll(self, pcm):
        self.calls += 1
        return self.result

    def probability(self, pcm):
        self.calls += 1
        return self.result


class ProtocolTests(unittest.TestCase):
    def test_stream_result_and_error_use_same_bounded_contract(self):
        for result in [Success(0.8), Failure(ErrorCode.INFERENCE_FAILED)]:
            adapter = Adapter(result)
            source = io.BytesIO(bytes(192 * 4) + struct.pack("<I", 2560) + bytes(2560 * 4))
            output = io.StringIO()
            with self.assertRaises(EOFError):
                serve(adapter, WorkerMode.STREAM, source, output)
            replies = [json.loads(line) for line in output.getvalue().splitlines()]
            self.assertEqual(replies[0], {"ready": True, "protocol": 1})
            self.assertEqual(adapter.calls, 1)
            if isinstance(result, Failure):
                self.assertEqual(replies[1], {"error": ErrorCode.INFERENCE_FAILED})
            else:
                self.assertEqual(replies[1], {"probability": 0.8})

    def test_invalid_frame_never_reaches_adapter(self):
        adapter = Adapter(Success([]))
        with self.assertRaises(ValueError):
            serve(adapter, WorkerMode.ENROLL, io.BytesIO(struct.pack("<I", 999999)), io.StringIO())
        self.assertEqual(adapter.calls, 0)
