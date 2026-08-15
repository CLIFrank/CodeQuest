import json
import tempfile
import unittest
from pathlib import Path

from codequest.curriculum import QUESTS
from codequest.progress import Progress, ProgressStore


class ProgressTests(unittest.TestCase):
    def test_quests_unlock_in_order(self):
        progress = Progress()
        self.assertTrue(progress.is_unlocked(QUESTS[0].id))
        self.assertFalse(progress.is_unlocked(QUESTS[1].id))
        self.assertTrue(progress.complete(QUESTS[0].id, QUESTS[0].xp))
        self.assertTrue(progress.is_unlocked(QUESTS[1].id))
        self.assertFalse(progress.complete(QUESTS[0].id, QUESTS[0].xp))

    def test_tasks_and_progress_round_trip(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "progress.json"
            store = ProgressStore(path)
            progress = Progress()
            progress.complete(QUESTS[0].id, QUESTS[0].xp)
            task = progress.add_task("Practise variables")
            self.assertIsNotNone(task)
            task.done = True
            progress.code[QUESTS[0].id] = "print('saved')"
            store.save(progress)

            loaded = store.load()
            self.assertEqual(loaded.xp, QUESTS[0].xp)
            self.assertEqual(loaded.tasks[0].title, "Practise variables")
            self.assertTrue(loaded.tasks[0].done)
            self.assertEqual(loaded.code[QUESTS[0].id], "print('saved')")

    def test_invalid_save_returns_fresh_progress(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "progress.json"
            path.write_text("not json", encoding="utf-8")
            self.assertEqual(ProgressStore(path).load(), Progress())


if __name__ == "__main__":
    unittest.main()
