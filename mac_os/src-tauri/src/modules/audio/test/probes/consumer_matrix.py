"""Opt-in development spike. Reads BlackHole to /dev/null; never saves PCM."""

import argparse
import json
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path


def snapshot(probe, device_id, producer_pid):
    output = subprocess.check_output([str(probe)], text=True)
    candidates = set()
    producer_active = False
    for line in output.splitlines():
        match = re.fullmatch(
            r"pid=(\d+) input=(\d+) output=(\d+) inputs\(status=0\)=([\d,]*) outputs\(status=0\)=([\d,]*)",
            line,
        )
        if not match:
            raise RuntimeError("Unknown process state; cannot infer zero consumers")
        pid, active, output_active, inputs, outputs = match.groups()
        output_devices = {int(value) for value in outputs.split(",") if value}
        if int(pid) == producer_pid and int(output_active) and device_id in output_devices:
            producer_active = True
        devices = {int(value) for value in inputs.split(",") if value}
        if int(pid) != producer_pid and int(active) and device_id in devices:
            candidates.add(int(pid))
    return candidates, producer_active


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--producer-pid", type=int, required=True)
    parser.add_argument("--device-id", type=int, required=True)
    args = parser.parse_args()
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("FFmpeg is required only for this development spike")
    inventory = (
        subprocess.run(
            [ffmpeg, "-hide_banner", "-f", "avfoundation", "-list_devices", "true", "-i", ""],
            capture_output=True,
            timeout=20,
            check=False,
        )
        .stderr.decode(errors="replace")
        .split("AVFoundation audio devices:")[-1]
    )
    matches = re.findall(r"\[(\d+)\] BlackHole 2ch\s*$", inventory, re.MULTILINE)
    if len(matches) != 1:
        raise RuntimeError("Expected exactly one BlackHole 2ch input")
    children = []
    with tempfile.TemporaryDirectory(prefix="audio-consumers-") as directory:
        probe = Path(directory) / "processes"
        subprocess.run(
            [
                "clang",
                "-Wall",
                "-Wextra",
                "-Werror",
                str(Path(__file__).with_name("processes.c")),
                "-framework",
                "CoreAudio",
                "-o",
                str(probe),
            ],
            check=True,
        )

        def verify(label, expected):
            deadline = time.monotonic() + 5
            while True:
                actual, producer_active = snapshot(probe, args.device_id, args.producer_pid)
                if not producer_active:
                    raise AssertionError("Producer is not active; consumer matrix is inconclusive")
                if actual == expected:
                    print(json.dumps({"stage": label, "candidateConsumers": sorted(actual)}), flush=True)
                    return
                if time.monotonic() >= deadline:
                    raise AssertionError(f"{label}: expected {expected}, observed {actual}")
                time.sleep(0.1)

        try:
            verify("producer_only", set())
            for index in range(2):
                child = subprocess.Popen(
                    [
                        ffmpeg,
                        "-nostdin",
                        "-loglevel",
                        "error",
                        "-f",
                        "avfoundation",
                        "-i",
                        ":" + matches[0],
                        "-f",
                        "null",
                        "-",
                    ],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                children.append(child)
                verify(f"consumers_{index + 1}", {process.pid for process in children})
            children[0].kill()
            children[0].wait(timeout=5)
            verify("first_consumer_crashed", {children[1].pid})
            children[1].terminate()
            children[1].wait(timeout=5)
            verify("all_consumers_closed", set())
        finally:
            for child in children:
                if child.poll() is None:
                    child.kill()
                child.wait(timeout=5)


if __name__ == "__main__":
    main()
