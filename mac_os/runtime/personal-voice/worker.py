"""Bounded local worker protocol. Model details belong to the injected adapter."""

import contextlib
import json
import os
import struct
import sys
import threading
import time
from pathlib import Path

# Trusted, bundled Python source root. -I excludes user site packages and PYTHONPATH.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ports.personal_voice import PersonalVoiceAdapter  # noqa: E402
from ports.result import Failure  # noqa: E402
from ports.worker_mode import WorkerMode  # noqa: E402


def parent_watchdog(parent):
    while True:
        time.sleep(1)
        if os.getppid() != parent:
            os._exit(0)


def send(value):
    sys.stdout.write(json.dumps(value, allow_nan=False) + "\n")
    sys.stdout.flush()


def read_exact(size):
    data = bytearray()
    while len(data) < size:
        chunk = sys.stdin.buffer.read(size - len(data))
        if not chunk:
            raise EOFError
        data.extend(chunk)
    return bytes(data)


def serve(adapter: PersonalVoiceAdapter, mode: WorkerMode):
    send({"ready": True, "protocol": 1})
    if mode is WorkerMode.STREAM:
        result = adapter.set_embedding(read_exact(192 * 4))
        if isinstance(result, Failure):
            send({"error": result.error})
            return
    while True:
        size = struct.unpack("<I", read_exact(4))[0]
        expected = 160000 if mode is WorkerMode.ENROLL else 2560
        if size != expected:
            raise ValueError("invalid_frame_size")
        pcm = read_exact(size * 4)
        with contextlib.redirect_stdout(sys.stderr):
            result = adapter.enroll(pcm) if mode is WorkerMode.ENROLL else adapter.probability(pcm)
        if isinstance(result, Failure):
            send({"error": result.error})
        else:
            send({"embedding" if mode is WorkerMode.ENROLL else "probability": result.value})


def main():
    parent = int(sys.argv[3])
    if parent <= 1 or os.getppid() != parent:
        return
    threading.Thread(target=parent_watchdog, args=(parent,), daemon=True).start()
    # Supervise before importing/loading the provider, which can take significant time.
    from adapters.personal_voice.nomo_adapter import NomoAdapter

    root = Path(sys.argv[1]).resolve()
    mode = WorkerMode(sys.argv[2])
    with contextlib.redirect_stdout(sys.stderr):
        result = NomoAdapter.create(root, Path(__file__).with_name("artifacts.json"))
    if isinstance(result, Failure):
        send({"error": result.error})
        return
    serve(result.value, mode)


if __name__ == "__main__":
    try:
        main()
    except EOFError:
        pass
    except Exception:  # noqa: BLE001 - do not disclose voice data in vendor errors
        send({"error": "personal_voice_inference_failed"})
        sys.exit(1)
