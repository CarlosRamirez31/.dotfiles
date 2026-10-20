"""Exercise the actual worker with supplied PCM16 mono 16 kHz fixtures; never opens a microphone."""

import argparse
import array
import json
import select
import statistics
import struct
import subprocess
import time
import wave
from pathlib import Path


def read_reply(process, timeout=120):
    if not select.select([process.stdout], [], [], timeout)[0]:
        raise TimeoutError("Worker did not respond")
    reply = json.loads(process.stdout.readline())
    if "error" in reply:
        raise RuntimeError(reply["error"])
    return reply


def read_wav(path):
    with wave.open(str(path)) as source:
        assert source.getnchannels() == 1 and source.getsampwidth() == 2 and source.getframerate() == 16000
        return [
            value / 32768
            for value in struct.unpack(f"<{source.getnframes()}h", source.readframes(source.getnframes()))
        ]


def start(root, mode):
    script = Path(__file__).with_name("worker.py")
    child = subprocess.Popen(
        [str(root / "venv/bin/python"), "-I", str(script), str(root), mode],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    try:
        assert read_reply(child)["ready"]
        return child
    except Exception:
        child.kill()
        child.wait()
        raise


def send(child, pcm):
    child.stdin.write(struct.pack("<I", len(pcm)))
    child.stdin.write(array.array("f", pcm).tobytes())
    child.stdin.flush()
    return read_reply(child)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--enroll", type=Path, required=True)
    parser.add_argument("--test", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    enrollment = read_wav(args.enroll)
    # Upstream's short fixture is repeated only to exercise the ten-second wire contract.
    enrollment = (enrollment * (160000 // len(enrollment) + 1))[:160000]
    child = start(root, "enroll")
    try:
        embedding = send(child, enrollment)["embedding"]
        assert len(embedding) == 192
    finally:
        child.kill()
        child.wait()
    child = start(root, "stream")
    probabilities, durations = [], []
    try:
        child.stdin.write(array.array("f", embedding).tobytes())
        child.stdin.flush()
        pcm = read_wav(args.test)
        for offset in range(0, len(pcm) - 2559, 2560):
            started = time.perf_counter()
            probability = send(child, pcm[offset : offset + 2560])["probability"]
            durations.append((time.perf_counter() - started) * 1000)
            assert 0 <= probability <= 1
            probabilities.append(probability)
    finally:
        child.kill()
        child.wait()
    print(
        json.dumps(
            {
                "frames": len(probabilities),
                "probability_min": min(probabilities),
                "probability_max": max(probabilities),
                "inference_median_ms": statistics.median(durations),
                "inference_max_ms": max(durations),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
