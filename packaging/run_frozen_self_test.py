"""Run the built application's non-interactive release smoke test."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--executable", type=Path, required=True)
    args = parser.parse_args()
    executable = args.executable.resolve()
    if not executable.is_file():
        raise FileNotFoundError(executable)

    startupinfo = None
    creationflags = 0
    if sys.platform == "win32":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        creationflags = subprocess.CREATE_NO_WINDOW
    result = subprocess.run(
        [str(executable), "--codequest-self-test"],
        timeout=30,
        startupinfo=startupinfo,
        creationflags=creationflags,
        check=False,
    )
    if result.returncode:
        raise SystemExit(result.returncode)
    print(f"Frozen self-test passed: {executable}")


if __name__ == "__main__":
    main()
