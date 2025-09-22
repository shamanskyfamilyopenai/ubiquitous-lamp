"""Persistence helpers for the schedule manager."""
from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Dict, List, Iterable

from .models import RecurringEvent, SingleEvent, Task


class DataStore:
    """Simple JSON-backed store for schedule data."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write({"recurring_events": [], "single_events": [], "tasks": []})

    # ------------------------------------------------------------------
    # Loading utilities
    # ------------------------------------------------------------------
    def load(self) -> Dict[str, List[dict]]:
        with self.path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _write(self, data: Dict[str, List[dict]]) -> None:
        with self.path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, sort_keys=True)

    # ------------------------------------------------------------------
    # Event helpers
    # ------------------------------------------------------------------
    def list_recurring(self) -> List[RecurringEvent]:
        data = self.load()["recurring_events"]
        return [RecurringEvent.from_dict(item) for item in data]

    def list_single(self) -> List[SingleEvent]:
        data = self.load()["single_events"]
        return [SingleEvent.from_dict(item) for item in data]

    def list_tasks(self) -> List[Task]:
        data = self.load()["tasks"]
        return [Task.from_dict(item) for item in data]

    def add_recurring(self, event: RecurringEvent) -> RecurringEvent:
        data = self.load()
        data["recurring_events"].append(event.to_dict())
        self._write(data)
        return event

    def add_single(self, event: SingleEvent) -> SingleEvent:
        data = self.load()
        data["single_events"].append(event.to_dict())
        self._write(data)
        return event

    def add_task(self, task: Task) -> Task:
        data = self.load()
        data["tasks"].append(task.to_dict())
        self._write(data)
        return task

    def replace(self, *, recurring: Iterable[RecurringEvent], single: Iterable[SingleEvent], tasks: Iterable[Task]) -> None:
        data = {
            "recurring_events": [event.to_dict() for event in recurring],
            "single_events": [event.to_dict() for event in single],
            "tasks": [task.to_dict() for task in tasks],
        }
        self._write(data)

    # ------------------------------------------------------------------
    # ID helpers
    # ------------------------------------------------------------------
    @staticmethod
    def new_id(prefix: str) -> str:
        return f"{prefix}-{uuid.uuid4().hex[:8]}"


def load_store(path: str | Path) -> DataStore:
    return DataStore(Path(path))
