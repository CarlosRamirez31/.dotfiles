"""Prepare the development runtime. No global installs, unpinned packages or automatic inference downloads."""

import argparse
import hashlib
import json
import platform
import subprocess
import sys
import urllib.request
import venv
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=Path)
    args = parser.parse_args()
    source = Path(__file__).resolve().parent
    if sys.version_info[:2] != (3, 14) or platform.machine() != "arm64" or sys.platform != "darwin":
        raise SystemExit("This development lock supports CPython 3.14 on macOS arm64 only.")
    root = (args.target or source.parents[1] / ".runtime/personal-voice").resolve()
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    if not (root / "venv/bin/python").exists():
        venv.create(root / "venv", with_pip=True)
    subprocess.run(
        [
            str(root / "venv/bin/python"),
            "-m",
            "pip",
            "install",
            "--require-hashes",
            "--only-binary=:all:",
            "-r",
            str(source / "requirements-arm64.lock"),
        ],
        check=True,
    )
    for artifact in json.loads((source / "artifacts.json").read_text())["artifacts"]:
        target = root / artifact["path"]
        if (
            target.is_file()
            and hashlib.file_digest(target.open("rb"), "sha256").hexdigest() == artifact["sha256"]
        ):
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(target.suffix + ".download")
        try:
            digest = hashlib.sha256()
            size = 0
            with (
                urllib.request.urlopen(artifact["url"], timeout=60) as response,
                temporary.open("wb") as output,
            ):
                while chunk := response.read(1024 * 1024):
                    size += len(chunk)
                    if size > artifact["bytes"]:
                        raise ValueError("Artifact exceeds pinned size")
                    output.write(chunk)
                    digest.update(chunk)
            if size != artifact["bytes"] or digest.hexdigest() != artifact["sha256"]:
                raise ValueError("Artifact does not match pinned manifest")
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
    print("Private development runtime prepared. No microphone was opened.")


if __name__ == "__main__":
    main()
