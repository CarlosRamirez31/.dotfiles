"""Opt-in BlackHole receiver. Keeps PCM only in memory; emits numeric measurements."""

import argparse
import array
import json
import math
import re
import select
import shutil
import subprocess
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=int, default=8, choices=range(4, 61))
    parser.add_argument("--expect", choices=["signal", "silence", "observe"], default="observe")
    parser.add_argument(
        "--speak", action="store_true", help="Play a fixed synthetic phrase through current output"
    )
    args = parser.parse_args()
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("Install ffmpeg separately to run this opt-in measurement")
    inventory = subprocess.run(
        [ffmpeg, "-hide_banner", "-f", "avfoundation", "-list_devices", "true", "-i", ""],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        timeout=20,
        check=False,
    )
    audio = inventory.stderr.decode(errors="replace").split("AVFoundation audio devices:")[-1]
    matches = re.findall(r"\[(\d+)\] BlackHole 2ch\s*$", audio, flags=re.MULTILINE)
    if len(matches) != 1:
        raise RuntimeError("BlackHole 2ch must be installed and visible as an audio input")
    process = subprocess.Popen(
        [
            ffmpeg,
            "-hide_banner",
            "-nostdin",
            "-loglevel",
            "error",
            "-f",
            "avfoundation",
            "-i",
            ":" + matches[0],
            "-ac",
            "2",
            "-ar",
            "48000",
            "-f",
            "f32le",
            "pipe:1",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    speech = None
    started = last = time.monotonic()
    pending = b""
    total = count = 0
    total_peak = energy = peak = 0.0
    try:
        while time.monotonic() - started < args.seconds:
            if process.poll() is not None:
                raise RuntimeError("Receiver exited before completing measurement")
            if args.speak and speech is None and time.monotonic() - started > 3:
                speech = subprocess.Popen(
                    [
                        "/usr/bin/say",
                        "Esta es una prueba local del micrófono. Uno, dos, tres, cuatro, cinco.",
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            ready, _, _ = select.select([process.stdout], [], [], 0.2)
            if ready:
                chunk = process.stdout.read1(32768)
                if not chunk:
                    raise RuntimeError("Receiver returned EOF")
                pending += chunk
                end = len(pending) // 4 * 4
                samples = array.array("f")
                samples.frombytes(pending[:end])
                pending = pending[end:]
                if any(not math.isfinite(value) for value in samples):
                    raise RuntimeError("Invalid PCM received")
                total += len(samples)
                count += len(samples)
                energy += sum(value * value for value in samples)
                peak = max(peak, max((abs(value) for value in samples), default=0.0))
            now = time.monotonic()
            if now - last >= 1:
                print(
                    json.dumps(
                        {
                            "seconds": round(now - started, 2),
                            "samples": count,
                            "rms": math.sqrt(energy / max(1, count)),
                            "peak": peak,
                        }
                    ),
                    flush=True,
                )
                total_peak = max(total_peak, peak)
                count = 0
                energy = peak = 0.0
                last = now
        total_peak = max(total_peak, peak)
    finally:
        if speech and speech.poll() is None:
            speech.terminate()
            speech.wait(timeout=3)
        process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=3)
        error = process.stderr.read().decode(errors="replace")
    # Frame count is a liveness check, not proof of latency or zero dropped input frames.
    if total < 48000 * 2 * args.seconds * 0.5:
        raise RuntimeError("Insufficient received PCM for the requested measurement")
    if args.expect == "signal" and total_peak <= 0.00001:
        raise RuntimeError("No nonzero filtered signal reached BlackHole")
    if args.expect == "silence" and total_peak > 0.000001:
        raise RuntimeError("BlackHole was not silent after stopping the producer")
    if error:
        raise RuntimeError("Receiver reported an audio error")
    print(
        json.dumps({"result": "passed", "expected": args.expect, "total_samples": total, "peak": total_peak}),
        flush=True,
    )


if __name__ == "__main__":
    main()
