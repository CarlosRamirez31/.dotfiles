"""Opt-in macOS process checks. Uses Keychain and loopback; never opens a microphone."""

import json
import os
import secrets
import select
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[4]
BINARY = ROOT / "src-tauri/target/debug/mac_os"
RUNTIME = ROOT / ".runtime/personal-voice"
WORKER = ROOT / "runtime/personal-voice/worker.py"


def reply(process, timeout=30):
    if not select.select([process.stdout], [], [], timeout)[0]:
        raise TimeoutError("process handshake timed out")
    return json.loads(process.stdout.readline())


def spawn(arguments):
    return subprocess.Popen(
        arguments, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
    )


def launch(directory):
    return {
        "directory": str(directory),
        "voice_runtime": str(RUNTIME),
        "voice_script": str(WORKER),
        "token": secrets.token_hex(32),
        "options": {
            "logging": {"retention_days": 30, "cleanup_seconds": 3600},
            "operations": {"max_pending": 16, "max_operations": 10000, "event_batch": 64},
            "voice": {
                "load_seconds": 120,
                "inference_seconds": 2,
                "enroll_seconds": 60,
                "threshold": 0.7,
                "runtime": None,
            },
            "startup_seconds": 30,
            "shutdown_seconds": 5,
            "reconnect_ms": 1500,
        },
    }


def start_service(config):
    process = spawn([str(BINARY), "--local-service"])
    try:
        process.stdin.write(json.dumps(config).encode() + b"\n")
        process.stdin.flush()
        info = reply(process)
        assert info["protocolVersion"] == 1 and info["token"] == config["token"]
        assert info["endpoint"].startswith("http://127.0.0.1:")
        return process, info
    except BaseException:
        terminate(process)
        raise


def terminate(process):
    if process.poll() is None:
        process.kill()
    process.wait(timeout=5)
    for pipe in (process.stdin, process.stdout):
        if pipe and not pipe.closed:
            pipe.close()


def wait_gone(pid):
    started = time.monotonic()
    while time.monotonic() - started < 8:
        result = subprocess.run(["ps", "-p", str(pid), "-o", "stat="], capture_output=True, text=True)
        if not result.stdout.strip() or result.stdout.strip().startswith("Z"):
            return round(time.monotonic() - started, 3)
        time.sleep(0.05)
    raise AssertionError(f"child remains active: {pid}")


def owner(kind, directory):
    if kind == "service":
        child, _ = start_service(launch(directory))
    else:
        child = spawn(
            [str(RUNTIME / "venv/bin/python"), "-I", str(WORKER), str(RUNTIME), "enroll", str(os.getpid())]
        )
        try:
            if kind != "worker-loading":
                assert reply(child, 120)["ready"]
        except BaseException:
            terminate(child)
            raise
    try:
        print(json.dumps({"pid": child.pid}), flush=True)
        sys.stdin.buffer.read()
    finally:
        terminate(child)


def crash_owner(kind, directory):
    parent = spawn([sys.executable, "-I", str(Path(__file__).resolve()), "--owner", kind, str(directory)])
    child_pid = None
    gone = False
    try:
        child_pid = reply(parent, 150)["pid"]
        parent.kill()
        parent.wait(timeout=5)
        elapsed = wait_gone(child_pid)
        gone = True
        print(f"PASS {kind}: child stopped after owner SIGKILL in {elapsed}s", flush=True)
    finally:
        terminate(parent)
        if child_pid and not gone:
            try:
                os.kill(child_pid, 9)
            except ProcessLookupError:
                pass


def main():
    with tempfile.TemporaryDirectory(prefix="microphone-lifecycle-") as directory:
        config = launch(Path(directory))
        standalone = spawn([str(BINARY), "--local-service"])
        standalone.stdin.close()
        assert standalone.wait(timeout=5) != 0
        terminate(standalone)
        print("PASS standalone service rejects missing handshake", flush=True)
        service, info = start_service(config)
        try:
            duplicate = spawn([str(BINARY), "--local-service"])
            try:
                duplicate.stdin.write(json.dumps(config).encode() + b"\n")
                duplicate.stdin.flush()
                assert duplicate.wait(timeout=5) != 0
                assert service.poll() is None
            finally:
                terminate(duplicate)
            print("PASS duplicate rejected; original remains alive", flush=True)
            request = Request(
                info["endpoint"] + "/v1/operations", headers={"Authorization": "Bearer " + info["token"]}
            )
            with urlopen(request, timeout=3) as response:
                assert response.status == 200
            started = time.monotonic()
            service.stdin.close()
            assert service.wait(timeout=8) == 0
            print(f"PASS EOF: service stopped in {time.monotonic() - started:.3f}s", flush=True)
        finally:
            terminate(service)
        service, _ = start_service(config)
        service.stdin.close()
        assert service.wait(timeout=8) == 0
        terminate(service)
        print("PASS restart releases lock and reopens encrypted state", flush=True)
        crash_owner("service", Path(directory))
        crash_owner("worker", Path(directory))
        crash_owner("worker-loading", Path(directory))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--owner":
        owner(sys.argv[2], Path(sys.argv[3]))
    else:
        main()
