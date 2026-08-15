"""CodeQuest application entry point.

The worker and self-test switches are intentionally handled before importing
Pygame. A frozen PyInstaller build re-launches this same executable when it
needs to run learner code in a child process.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path


RUNNER_SWITCH = "--codequest-runner-worker"
SELF_TEST_SWITCH = "--codequest-self-test"


def _run_self_test() -> int:
    """Exercise the frozen code runner and two headless UI frames."""
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

    from codequest.runner import run_code

    result = run_code("print(6 * 7)")
    if not result.ok or result.output.strip() != "42":
        return 2

    from codequest.app import CodeQuestApp
    from codequest.progress import ProgressStore

    with tempfile.TemporaryDirectory(prefix="codequest-self-test-") as folder:
        store = ProgressStore(Path(folder) / "progress.json")
        CodeQuestApp(store).run(max_frames=2)
    return 0


def main() -> int:
    if RUNNER_SWITCH in sys.argv[1:]:
        from codequest.runner_worker import main as worker_main

        worker_main()
        return 0
    if SELF_TEST_SWITCH in sys.argv[1:]:
        return _run_self_test()

    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    from codequest.app import CodeQuestApp

    CodeQuestApp().run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
