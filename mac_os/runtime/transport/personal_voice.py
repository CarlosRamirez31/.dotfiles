"""Bounded worker transport. Depends only on the capability port and injected streams."""

import contextlib
import json
import struct
import sys

from ports.personal_voice import PersonalVoiceAdapter
from ports.result import Failure
from ports.worker_mode import WorkerMode


def send(value, output):
    output.write(json.dumps(value, allow_nan=False) + "\n")
    output.flush()


def read_exact(size, source):
    data = bytearray()
    while len(data) < size:
        chunk = source.read(size - len(data))
        if not chunk:
            raise EOFError
        data.extend(chunk)
    return bytes(data)


def serve(adapter: PersonalVoiceAdapter, mode: WorkerMode, source, output):
    send({"ready": True, "protocol": 1}, output)
    if mode is WorkerMode.STREAM:
        result = adapter.set_embedding(read_exact(192 * 4, source))
        if isinstance(result, Failure):
            send({"error": result.error}, output)
            return
    while True:
        size = struct.unpack("<I", read_exact(4, source))[0]
        expected = 160000 if mode is WorkerMode.ENROLL else 2560
        if size != expected:
            raise ValueError("invalid_frame_size")
        pcm = read_exact(size * 4, source)
        with contextlib.redirect_stdout(sys.stderr):
            result = adapter.enroll(pcm) if mode is WorkerMode.ENROLL else adapter.probability(pcm)
        if isinstance(result, Failure):
            send({"error": result.error}, output)
        else:
            send({"embedding" if mode is WorkerMode.ENROLL else "probability": result.value}, output)
