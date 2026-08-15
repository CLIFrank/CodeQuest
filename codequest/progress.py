"""Small JSON persistence layer for learner progress and personal tasks."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .curriculum import QUESTS


@dataclass
class LearnerTask:
    id: int
    title: str
    done: bool = False


@dataclass
class Progress:
    completed: list[str] = field(default_factory=list)
    xp: int = 0
    streak: int = 1
    tasks: list[LearnerTask] = field(default_factory=list)
    code: dict[str, str] = field(default_factory=dict)

    def is_unlocked(self, quest_id: str) -> bool:
        index = next(i for i, quest in enumerate(QUESTS) if quest.id == quest_id)
        return index == 0 or QUESTS[index - 1].id in self.completed

    def complete(self, quest_id: str, xp: int) -> bool:
        if quest_id in self.completed:
            return False
        self.completed.append(quest_id)
        self.xp += xp
        return True

    def add_task(self, title: str) -> LearnerTask | None:
        clean = title.strip()
        if not clean:
            return None
        new_id = max((task.id for task in self.tasks), default=0) + 1
        task = LearnerTask(new_id, clean[:80])
        self.tasks.append(task)
        return task


class ProgressStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or Path.home() / ".codequest" / "progress.json"

    def load(self) -> Progress:
        try:
            raw: dict[str, Any] = json.loads(self.path.read_text(encoding="utf-8"))
            valid_ids = {quest.id for quest in QUESTS}
            return Progress(
                completed=[str(q) for q in raw.get("completed", []) if q in valid_ids],
                xp=max(0, int(raw.get("xp", 0))),
                streak=max(1, int(raw.get("streak", 1))),
                tasks=[
                    LearnerTask(int(item["id"]), str(item["title"]), bool(item.get("done")))
                    for item in raw.get("tasks", [])
                    if "id" in item and "title" in item
                ],
                code={
                    str(key): str(value)
                    for key, value in raw.get("code", {}).items()
                    if key in valid_ids
                },
            )
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return Progress()

    def save(self, progress: Progress) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "completed": progress.completed,
            "xp": progress.xp,
            "streak": progress.streak,
            "tasks": [asdict(task) for task in progress.tasks],
            "code": progress.code,
        }
        temp = self.path.with_suffix(".tmp")
        temp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        temp.replace(self.path)
