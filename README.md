# CodeQuest

CodeQuest is a polished Pygame desktop application that helps beginners learn
Python through short story-driven missions. Learners write real Python in the
built-in editor, run it, compare its output with the goal, earn XP, and unlock
new levels.

## Included experience

- Eight progressive puzzles covering output, variables, numbers, loops,
  conditionals, lists, functions, and dictionaries
- Friendly code editor with line numbers, syntax colours, automatic indentation,
  undo, paste, and a live output console
- Run and check flows with readable Python errors, expected-output feedback, and
  optional hints
- Quest unlocking, XP, learner levels, completion celebrations, and saved code
- A personal task list so learners can create and check off practice goals
- Local JSON persistence between sessions

## Run the app

Python 3.10 or newer is recommended.

```powershell
python -m pip install -r requirements.txt
python main.py
```

Pygame 2.6.1 is already available in the current development environment.

## Controls

- Click a mission card to open it.
- Type directly in the editor. `Tab` inserts four spaces and new lines inherit
  indentation.
- Use **Run** to preview output and **Check** to submit it.
- Press `Ctrl+Enter` to check without leaving the keyboard.
- Press `Ctrl+Z` to undo or `Ctrl+V` to paste.
- Press `Esc` to return to the home base.

Progress is stored at `~/.codequest/progress.json`. Delete that file to reset a
local learner profile.

## Project layout

```text
main.py                       Application entry point
codequest/app.py              Screens, navigation, and game loop
codequest/widgets.py          Buttons, text input, and code editor
codequest/curriculum.py       Data-driven puzzle definitions
codequest/runner.py           Validation and subprocess orchestration
codequest/runner_worker.py    Restricted learning runtime
codequest/progress.py         JSON-backed learner state
tests/                        Curriculum and persistence checks
```

## Verification

Run the automated checks with:

```powershell
python -m unittest discover -s tests -v
```

Learner code runs in a separate process with a two-second timeout, no imports,
and a deliberately small set of built-ins. This prevents common accidents and
keeps puzzle behaviour predictable. It is an educational guardrail rather than
a hardened security boundary; deploy an operating-system or container sandbox
before accepting untrusted code in a shared or online environment.

## Build a distributable application

Phase 1 release packaging is documented in
[`packaging/README.md`](packaging/README.md). A local Windows build can be
created with PyInstaller, while the GitHub Actions workflow builds Windows,
Linux, and macOS archives and publishes them when a version tag is pushed.

The frozen build contains a non-interactive `--codequest-self-test` mode that
verifies both Pygame startup and learner-code execution from the packaged
executable before a release is uploaded.

## License

CodeQuest is available under the [MIT License](LICENSE).
