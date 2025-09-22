"""Utilities for building schedule outputs."""
from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import List, Sequence

from .models import DAYS_OF_WEEK, EventOccurrence, RecurringEvent, SingleEvent, Task

WEEKDAY_TO_INDEX = {name: index for index, name in enumerate(DAYS_OF_WEEK)}


def generate_occurrences(
    *,
    start_date: date,
    days: int,
    recurring_events: Sequence[RecurringEvent],
    single_events: Sequence[SingleEvent],
    tasks: Sequence[Task],
) -> List[EventOccurrence]:
    """Return all occurrences that happen during the given window."""

    window_start = datetime.combine(start_date, datetime.min.time())
    window_end = window_start + timedelta(days=days)
    occurrences: List[EventOccurrence] = []

    # Expand recurring events
    for event in recurring_events:
        occurrences.extend(_expand_recurring_event(event, start_date, days))

    # Add single events that intersect the window
    for event in single_events:
        if event.end < window_start or event.start >= window_end:
            continue
        occurrences.append(
            EventOccurrence(
                start=event.start,
                end=event.end,
                title=event.title,
                category=event.category,
                source_id=event.id,
                source_type="single",
                location=event.location,
                notes=event.notes,
            )
        )

    # Represent tasks as all-day events on their due date
    for task in tasks:
        if not task.due:
            continue
        due_date = task.due.date()
        if not (start_date <= due_date < start_date + timedelta(days=days)):
            continue
        all_day_start = datetime.combine(due_date, datetime.min.time())
        occurrences.append(
            EventOccurrence(
                start=all_day_start,
                end=None,
                title=task.title,
                category=task.category,
                source_id=task.id,
                source_type="task",
                location=None,
                notes=task.notes,
            )
        )

    occurrences.sort()
    return occurrences


def _expand_recurring_event(event: RecurringEvent, start_date: date, days: int) -> List[EventOccurrence]:
    occurrences: List[EventOccurrence] = []
    for offset in range(days):
        current_date = start_date + timedelta(days=offset)
        if current_date < event.start_date:
            continue
        if event.end_date and current_date > event.end_date:
            continue
        weekday = current_date.strftime("%A").upper()
        if weekday not in event.days_of_week:
            continue
        start_dt = datetime.combine(current_date, event.start_time)
        end_dt = datetime.combine(current_date, event.end_time)
        occurrences.append(
            EventOccurrence(
                start=start_dt,
                end=end_dt,
                title=event.title,
                category=event.category,
                source_id=event.id,
                source_type="recurring",
                location=event.location,
                notes=event.notes,
            )
        )
    return occurrences


def build_text_schedule(start_date: date, occurrences: Sequence[EventOccurrence]) -> str:
    """Return a plain-text schedule grouped by day."""

    days: dict[date, List[EventOccurrence]] = defaultdict(list)
    for occurrence in occurrences:
        day = occurrence.start.date()
        days[day].append(occurrence)

    lines: List[str] = []
    sorted_days = sorted(days)
    if sorted_days:
        end_date = sorted_days[-1]
        lines.append(
            f"Schedule for {start_date.strftime('%A, %b %d, %Y')} "
            f"to {end_date.strftime('%A, %b %d, %Y')}"
        )
        lines.append("")
    else:
        lines.append(f"Schedule starting {start_date.strftime('%A, %b %d, %Y')}")
        lines.append("No events scheduled.")
        return "\n".join(lines)

    for day in sorted_days:
        day_occurrences = sorted(days[day])
        lines.append(day.strftime("%A, %b %d"))
        if not day_occurrences:
            lines.append("  (No events)")
            lines.append("")
            continue
        for occurrence in day_occurrences:
            block = occurrence.to_display_block().split("\n")
            lines.extend([f"  {line}" for line in block])
            lines.append("")
    if lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)
