"""Command line interface for managing your schedule data."""
from __future__ import annotations

import argparse
from datetime import date, datetime, time
from pathlib import Path
from typing import Iterable, List

from schedule.generator import build_text_schedule, generate_occurrences
from schedule.models import DAYS_OF_WEEK, RecurringEvent, SingleEvent, Task
from schedule.store import DataStore, load_store

DEFAULT_DATA_FILE = Path("data/events.json")
DEFAULT_OUTPUT_FILE = Path("schedule_next_week.txt")


# ---------------------------------------------------------------------------
# Argument parsing helpers
# ---------------------------------------------------------------------------

def _parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def _parse_datetime(value: str) -> datetime:
    formats = ["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M"]
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise argparse.ArgumentTypeError(
        f"Could not parse datetime '{value}'. Expected format YYYY-MM-DD HH:MM."
    )


def _parse_time(value: str) -> time:
    try:
        return datetime.strptime(value, "%H:%M").time()
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Use 24-hour HH:MM format for times.") from exc


def _parse_days(value: str) -> List[str]:
    parts = [part.strip().upper() for part in value.split(",")]
    normalized = []
    for part in parts:
        match = _normalize_weekday(part)
        if not match:
            raise argparse.ArgumentTypeError(
                f"Unknown weekday '{part}'. Use names like Mon, Tuesday, etc."
            )
        normalized.append(match)
    return normalized


def _normalize_weekday(value: str) -> str | None:
    value = value.upper()
    for name in DAYS_OF_WEEK:
        if name.startswith(value):
            return name
    return None


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-file",
        type=Path,
        default=DEFAULT_DATA_FILE,
        help=f"Path to the JSON data file (default: {DEFAULT_DATA_FILE})",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    add_recurring = subparsers.add_parser("add-recurring", help="Add a recurring weekly event")
    add_recurring.add_argument("title", help="Title of the event")
    add_recurring.add_argument("category", help="Category tag (class, chore, etc.)")
    add_recurring.add_argument("start_date", type=_parse_date, help="First date the event occurs")
    add_recurring.add_argument("start_time", type=_parse_time, help="Start time (HH:MM, 24h)")
    add_recurring.add_argument("end_time", type=_parse_time, help="End time (HH:MM, 24h)")
    add_recurring.add_argument(
        "days",
        type=_parse_days,
        help="Comma separated weekdays (e.g. Mon,Wed,Fri)",
    )
    add_recurring.add_argument(
        "--end-date",
        type=_parse_date,
        help="Optional last date for the recurrence",
    )
    add_recurring.add_argument("--location", help="Optional location", default=None)
    add_recurring.add_argument("--notes", help="Optional notes", default=None)

    add_single = subparsers.add_parser("add-single", help="Add a single event")
    add_single.add_argument("title")
    add_single.add_argument("category")
    add_single.add_argument("start", type=_parse_datetime)
    add_single.add_argument("end", type=_parse_datetime)
    add_single.add_argument("--location", default=None)
    add_single.add_argument("--notes", default=None)

    add_task = subparsers.add_parser("add-task", help="Add a task with an optional due date")
    add_task.add_argument("title")
    add_task.add_argument("category")
    add_task.add_argument("--due", type=_parse_datetime, default=None)
    add_task.add_argument("--notes", default=None)

    list_parser = subparsers.add_parser("list", help="List all stored items")

    generate = subparsers.add_parser("generate", help="Generate the next week's schedule")
    generate.add_argument(
        "--start-date",
        type=_parse_date,
        default=date.today,
        help="First day of the window (defaults to today)",
    )
    generate.add_argument(
        "--days",
        type=int,
        default=7,
        help="How many days to include (default: 7)",
    )
    generate.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_FILE,
        help=f"Where to write the text schedule (default: {DEFAULT_OUTPUT_FILE})",
    )

    import_plain = subparsers.add_parser(
        "import-plain",
        help="Import one-time events from a simple text format",
    )
    import_plain.add_argument("path", type=Path, help="File containing events to import")

    return parser


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------

def handle_add_recurring(args: argparse.Namespace, store: DataStore) -> None:
    event = RecurringEvent(
        id=store.new_id("rec"),
        title=args.title,
        category=args.category,
        start_date=args.start_date,
        start_time=args.start_time,
        end_time=args.end_time,
        days_of_week=args.days,
        end_date=args.end_date,
        location=args.location,
        notes=args.notes,
    )
    store.add_recurring(event)
    print(f"Added recurring event '{event.title}' on {', '.join(event.days_of_week)}")


def handle_add_single(args: argparse.Namespace, store: DataStore) -> None:
    event = SingleEvent(
        id=store.new_id("evt"),
        title=args.title,
        category=args.category,
        start=args.start,
        end=args.end,
        location=args.location,
        notes=args.notes,
    )
    store.add_single(event)
    print(f"Added single event '{event.title}' on {event.start:%Y-%m-%d %H:%M}")


def handle_add_task(args: argparse.Namespace, store: DataStore) -> None:
    task = Task(
        id=store.new_id("task"),
        title=args.title,
        category=args.category,
        due=args.due,
        notes=args.notes,
    )
    store.add_task(task)
    if task.due:
        print(f"Added task '{task.title}' due {task.due:%Y-%m-%d %H:%M}")
    else:
        print(f"Added task '{task.title}' with no due date")


def handle_list(args: argparse.Namespace, store: DataStore) -> None:
    recurring = store.list_recurring()
    single = store.list_single()
    tasks = store.list_tasks()

    print("Recurring events:")
    if not recurring:
        print("  (none)")
    for event in recurring:
        days = ", ".join(event.days_of_week)
        end_date = f" until {event.end_date.isoformat()}" if event.end_date else ""
        print(
            f"  - {event.title} [{event.category}] {days} "
            f"{event.start_time.strftime('%H:%M')} - {event.end_time.strftime('%H:%M')}" + end_date
        )

    print("\nSingle events:")
    if not single:
        print("  (none)")
    for event in single:
        print(
            f"  - {event.title} [{event.category}] {event.start:%Y-%m-%d %H:%M}"
            f" - {event.end:%Y-%m-%d %H:%M}"
        )

    print("\nTasks:")
    if not tasks:
        print("  (none)")
    for task in tasks:
        due = task.due.strftime("%Y-%m-%d %H:%M") if task.due else "(no due date)"
        print(f"  - {task.title} [{task.category}] due {due}")


def handle_generate(args: argparse.Namespace, store: DataStore) -> None:
    start_date = args.start_date() if callable(args.start_date) else args.start_date
    occurrences = generate_occurrences(
        start_date=start_date,
        days=args.days,
        recurring_events=store.list_recurring(),
        single_events=store.list_single(),
        tasks=store.list_tasks(),
    )
    text = build_text_schedule(start_date, occurrences)
    args.output.write_text(text, encoding="utf-8")
    print(f"Wrote schedule to {args.output}")


def handle_import_plain(args: argparse.Namespace, store: DataStore) -> None:
    lines = args.path.read_text(encoding="utf-8").splitlines()
    imported = 0
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        event = _parse_plain_event(line, store)
        if event:
            store.add_single(event)
            imported += 1
    print(f"Imported {imported} events from {args.path}")


def _parse_plain_event(line: str, store: DataStore) -> SingleEvent | None:
    """Parse the simple "YYYY-MM-DD HH:MM-HH:MM | Title | Category | Location | Notes" format."""

    parts = [part.strip() for part in line.split("|")]
    if len(parts) < 2:
        raise ValueError(
            "Each line must have at least date/time and title separated by '|'."
        )
    timing = parts[0]
    title = parts[1]
    category = parts[2] if len(parts) > 2 and parts[2] else "general"
    location = parts[3] if len(parts) > 3 and parts[3] else None
    notes = parts[4] if len(parts) > 4 and parts[4] else None

    try:
        date_part, times_part = timing.split()
        start_time_str, end_time_str = times_part.split("-", 1)
    except ValueError as exc:
        raise ValueError(
            "Timing column must look like 'YYYY-MM-DD HH:MM-HH:MM'"
        ) from exc

    start_dt = _parse_datetime(f"{date_part} {start_time_str}")
    end_dt = _parse_datetime(f"{date_part} {end_time_str}")

    return SingleEvent(
        id=store.new_id("evt"),
        title=title,
        category=category,
        start=start_dt,
        end=end_dt,
        location=location,
        notes=notes,
    )


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

def main(argv: Iterable[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    store = load_store(args.data_file)

    command = args.command.replace("-", "_")
    handler = globals().get(f"handle_{command}")
    if not handler:
        raise SystemExit(f"Unknown command {args.command}")
    handler(args, store)


if __name__ == "__main__":
    main()
