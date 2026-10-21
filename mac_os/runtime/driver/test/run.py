"""Compile upstream split-device counters in a process; never installs a HAL driver."""

import argparse
import hashlib
import subprocess
import tempfile
from pathlib import Path

SOURCE_SHA256 = "5194703e8923713d15159b951b8fe9a8be08e7c0fb7c05b17c8e865e4c2effb6"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    source = args.source.resolve(strict=True)
    with source.open("rb") as content:
        if hashlib.file_digest(content, "sha256").hexdigest() != SOURCE_SHA256:
            raise ValueError("Upstream source does not match BlackHole 0.7.1 spike")
    with tempfile.TemporaryDirectory(prefix="driver-split-") as directory:
        executable = Path(directory) / "split-test"
        subprocess.run(
            [
                "clang",
                "-fblocks",
                f'-DMIC_DRIVER_SOURCE="{source}"',
                str(Path(__file__).with_name("split_devices.c")),
                "-framework",
                "CoreAudio",
                "-framework",
                "CoreFoundation",
                "-framework",
                "Accelerate",
                "-o",
                str(executable),
            ],
            check=True,
        )
        subprocess.run([str(executable)], check=True)


if __name__ == "__main__":
    main()
