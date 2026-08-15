"""Validate and execute learner code in a short-lived subprocess."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RunResult:
    ok: bool
    output: str = ""
    error: str = ""


FORBIDDEN_CALLS = {
    "breakpoint",
    "compile",
    "eval",
    "exec",
    "globals",
    "input",
    "locals",
    "open",
    "vars",
    "__import__",
}

RUNNER_SWITCH = "--codequest-runner-worker"


def validate_code(code: str) -> str | None:
    if len(code) > 10_000:
        return "Your program is too long for this puzzle."
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None  # The worker formats the useful syntax error.
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            return "Imports are switched off inside puzzle levels."
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            return "Special double-underscore attributes are not available in puzzles."
        if isinstance(node, ast.Name) and node.id.startswith("__"):
            return "Special double-underscore names are not available in puzzles."
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in FORBIDDEN_CALLS:
                return f"{node.func.id}() is not available inside puzzle levels."
    return None


def worker_command() -> list[str]:
    """Return a worker command for source and frozen application modes."""
    if getattr(sys, "frozen", False):
        return [sys.executable, RUNNER_SWITCH]
    worker = Path(__file__).with_name("runner_worker.py")
    return [sys.executable, "-I", str(worker)]


def run_code(code: str, timeout: float = 2.0) -> RunResult:
    validation_error = validate_code(code)
    if validation_error:
        return RunResult(False, error=validation_error)

    startupinfo = None
    creationflags = 0
    if sys.platform == "win32":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        creationflags = subprocess.CREATE_NO_WINDOW
    try:
        process = subprocess.run(
            worker_command(),
            input=code,
            capture_output=True,
            text=True,
            timeout=timeout,
            startupinfo=startupinfo,
            creationflags=creationflags,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return RunResult(False, error="Time limit reached. Check for an endless loop.")
    try:
        payload = json.loads(process.stdout)
        return RunResult(bool(payload["ok"]), str(payload["output"]), str(payload["error"]))
    except (json.JSONDecodeError, KeyError, TypeError):
        return RunResult(False, error="The code runner stopped unexpectedly. Try again.")
