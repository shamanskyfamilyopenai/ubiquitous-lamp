"""Data models for the schedule manager."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date, datetime, time, timedelta
from typing import List, Optional, Dict, Any

DAYS_OF_WEEK = [
    "MONDAY",
    "TUESDAY",
    "WEDNESDAY",
    "THURSDAY",
    "FRIDAY",
    "SATURDAY",
    "SUNDAY",
]


@dataclass
class RecurringEvent:
    """Model for an event that repeats every week on given days."""

    id: str
    title: str
    category: str
    start_date: date
    start_time: time
    end_time: time
    days_of_week: List[str]
    end_date: Optional[date] = None
    location: Optional[str] = None
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["start_date"] = self.start_date.isoformat()
        data["start_time"] = self.start_time.strftime("%H:%M")
        data["end_time"] = self.end_time.strftime("%H:%M")
        if self.end_date:
            data["end_date"] = self.end_date.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RecurringEvent":
        return cls(
            id=data["id"],
            title=data["title"],
            category=data["category"],
            start_date=date.fromisoformat(data["start_date"]),
            start_time=_parse_time(data["start_time"]),
            end_time=_parse_time(data["end_time"]),
            days_of_week=[day.upper() for day in data["days_of_week"]],
            end_date=date.fromisoformat(data["end_date"]) if data.get("end_date") else None,
            location=data.get("location"),
            notes=data.get("notes"),
        )


@dataclass
class SingleEvent:
    """Model for a one-off event."""

    id: str
    title: str
    category: str
    start: datetime
    end: datetime
    location: Optional[str] = None
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["start"] = self.start.isoformat()
        data["end"] = self.end.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SingleEvent":
        return cls(
            id=data["id"],
            title=data["title"],
            category=data["category"],
            start=datetime.fromisoformat(data["start"]),
            end=datetime.fromisoformat(data["end"]),
            location=data.get("location"),
            notes=data.get("notes"),
        )


@dataclass
class Task:
    """Model for a task with an optional due datetime."""

    id: str
    title: str
    category: str
    due: Optional[datetime] = None
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if self.due:
            data["due"] = self.due.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        due_value = data.get("due")
        return cls(
            id=data["id"],
            title=data["title"],
            category=data["category"],
            due=datetime.fromisoformat(due_value) if due_value else None,
            notes=data.get("notes"),
        )


@dataclass(order=True)
class EventOccurrence:
    """Concrete instance of an event happening at a specific time."""

    start: datetime
    end: Optional[datetime]
    title: str
    category: str
    source_id: str
    source_type: str
    location: Optional[str] = None
    notes: Optional[str] = None

    @property
    def duration(self) -> Optional[timedelta]:
        if self.start and self.end:
            return self.end - self.start
        return None

    def to_display_block(self) -> str:
        time_range = _format_time_range(self.start, self.end)
        parts = [f"{time_range} {self.title} [{self.category}] ({self.source_type})"]
        if self.location:
            parts.append(f"Location: {self.location}")
        if self.notes:
            parts.append(f"Notes: {self.notes}")
        return "\n".join(parts)


def _parse_time(value: str) -> time:
    hour, minute = [int(piece) for piece in value.split(":", 1)]
    return time(hour=hour, minute=minute)


def _format_time_range(start: datetime, end: Optional[datetime]) -> str:
    start_text = start.strftime("%I:%M %p").lstrip("0")
    if not end:
        return f"{start_text}-"
    end_text = end.strftime("%I:%M %p").lstrip("0")
    if start.date() != end.date():
        end_text = f"{end.strftime('%b %d')} {end_text}"
    return f"{start_text}-{end_text}"
