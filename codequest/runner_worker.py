"""Subprocess worker used by :mod:`codequest.runner`.

It deliberately exposes a small set of Python built-ins. This provides a calm
learning environment and prevents accidental file access, but it is not meant
to be a hardened operating-system security sandbox.
"""

from __future__ import annotations

import io
import json
import sys
import traceback
from contextlib import redirect_stdout


SAFE_BUILTINS = {
    "print": print,
    "range": range,
    "len": len,
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "list": list,
    "dict": dict,
    "set": set,
    "tuple": tuple,
    "enumerate": enumerate,
    "zip": zip,
    "sum": sum,
    "min": min,
    "max": max,
    "abs": abs,
    "round": round,
    "sorted": sorted,
}


def main() -> None:
    code = sys.stdin.read()
    output = io.StringIO()
    try:
        compiled = compile(code, "<learner-code>", "exec")
        with redirect_stdout(output):
            exec(compiled, {"__builtins__": SAFE_BUILTINS}, {})
        result = {"ok": True, "output": output.getvalue(), "error": ""}
    except Exception as exc:  # noqa: BLE001 - errors are reported to the learner
        lines = traceback.format_exception_only(type(exc), exc)
        result = {"ok": False, "output": output.getvalue(), "error": "".join(lines).strip()}
    sys.stdout.write(json.dumps(result))


if __name__ == "__main__":
    main()
