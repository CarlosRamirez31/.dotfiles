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
from adapters.personal_voice.nomo_adapter import NomoAdapter  # noqa: E402
from ports.personal_voice import PersonalVoiceAdapter  # noqa: E402


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


def serve(adapter: PersonalVoiceAdapter, mode: str):
    send({"ready": True, "protocol": 1})
    if mode == "stream":
        adapter.set_embedding(read_exact(192 * 4))
    while True:
        size = struct.unpack("<I", read_exact(4))[0]
        expected = 160000 if mode == "enroll" else 2560
        if size != expected:
            raise ValueError("invalid_frame_size")
        pcm = read_exact(size * 4)
        with contextlib.redirect_stdout(sys.stderr):
            result = (
                {"embedding": adapter.enroll(pcm)}
                if mode == "enroll"
                else {"probability": adapter.probability(pcm)}
            )
        send(result)


def main():
    root = Path(sys.argv[1]).resolve()
    mode = sys.argv[2]
    if mode not in {"enroll", "stream"}:
        raise ValueError("invalid_mode")
    threading.Thread(target=parent_watchdog, args=(os.getppid(),), daemon=True).start()
    with contextlib.redirect_stdout(sys.stderr):
        adapter = NomoAdapter(root, Path(__file__).with_name("artifacts.json"))
    serve(adapter, mode)


if __name__ == "__main__":
    try:
        main()
    except EOFError:
        pass
    except Exception:  # noqa: BLE001 - do not disclose voice data in vendor errors
        send({"error": "personal_voice_inference_failed"})
        sys.exit(1)
