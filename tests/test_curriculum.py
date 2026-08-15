import unittest
from unittest.mock import patch
import sys

from codequest.curriculum import QUESTS, normalise_output, output_matches
from codequest.runner import RUNNER_SWITCH, run_code, validate_code, worker_command


SOLUTIONS = {
    "signal": 'print("Hello, CodeQuest!")',
    "codename": 'hero = "Nova"\nprint(hero)',
    "fuel_math": "cell_a = 7\ncell_b = 5\nprint(cell_a + cell_b)",
    "countdown": 'for n in range(3, 0, -1):\n    print(n)\nprint("Blast off!")',
    "airlock": 'oxygen = 100\nif oxygen >= 80:\n    print("Airlock open")',
    "cargo": 'cargo = ["water", "food", "tools"]\nfor item in cargo:\n    print(item)',
    "translator": 'def greet(name):\n    return "Welcome, " + name\nprint(greet("Zed"))',
    "star_map": 'stars = {"Orion": 42, "Lyra": 17}\nprint(stars["Orion"])',
}


class CurriculumTests(unittest.TestCase):
    def test_every_quest_has_a_working_solution(self):
        self.assertEqual({quest.id for quest in QUESTS}, set(SOLUTIONS))
        for quest in QUESTS:
            with self.subTest(quest=quest.id):
                result = run_code(SOLUTIONS[quest.id])
                self.assertTrue(result.ok, result.error)
                self.assertTrue(output_matches(quest, result.output))

    def test_output_normalisation_only_ignores_trailing_space(self):
        self.assertEqual(normalise_output("a  \nb\n"), "a\nb")
        self.assertNotEqual(normalise_output("A"), normalise_output("a"))

    def test_runner_rejects_imports_and_file_access(self):
        self.assertIsNotNone(validate_code("import os"))
        self.assertIsNotNone(validate_code("open('notes.txt')"))

    def test_runner_reports_python_errors(self):
        result = run_code("print(missing_name)")
        self.assertFalse(result.ok)
        self.assertIn("NameError", result.error)

    def test_frozen_build_relaunches_itself_as_worker(self):
        with patch.object(sys, "frozen", True, create=True):
            self.assertEqual(worker_command(), [sys.executable, RUNNER_SWITCH])


if __name__ == "__main__":
    unittest.main()
