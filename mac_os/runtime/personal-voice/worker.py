"""Bounded local worker protocol. Model details belong to the injected adapter."""

import contextlib
import os
import sys
import threading
import time
from pathlib import Path

# Trusted, bundled Python source root. -I excludes user site packages and PYTHONPATH.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ports.result import Failure  # noqa: E402
from ports.worker_mode import WorkerMode  # noqa: E402
from transport.personal_voice import send, serve  # noqa: E402


def parent_watchdog(parent):
    while True:
        time.sleep(1)
        if os.getppid() != parent:
            os._exit(0)


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
        send({"error": result.error}, sys.stdout)
        return
    serve(result.value, mode, sys.stdin.buffer, sys.stdout)


if __name__ == "__main__":
    try:
        main()
    except EOFError:
        pass
    except Exception:  # noqa: BLE001 - do not disclose voice data in vendor errors
        send({"error": "personal_voice_inference_failed"}, sys.stdout)
        sys.exit(1)
