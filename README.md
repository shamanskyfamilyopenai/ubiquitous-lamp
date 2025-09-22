# ubiquitous-lamp

This repository provides a lightweight scheduling backend that writes a plain-text
agenda for the next week. The text output is designed to be easy for a front-end to
read and display while you send commands back (for example through a message box)
for Codex to update the schedule.

## Requirements

* Python 3.10 or newer (only uses the standard library)

## Project structure

```
.
├── data/events.json        # Persistent storage for all events and tasks
├── schedule/               # Core scheduling logic
│   ├── generator.py        # Expands events into concrete occurrences & builds text output
│   ├── models.py           # Dataclasses that describe events, tasks, and occurrences
│   └── store.py            # JSON-backed persistence helper
├── schedule_cli.py         # Command line interface for managing data
└── schedule_next_week.txt  # Created by the `generate` command (ignored until generated)
```

## Quick start

1. Add recurring classes or routines:

   ```bash
   python schedule_cli.py add-recurring "Biology 201" class 2023-09-04 09:00 10:15 Mon,Wed,Fri \
       --location "Science Hall 210" --notes "Lab on Wednesdays"
   ```

2. Import one-off events from a plain text file (see format below):

   ```bash
   python schedule_cli.py import-plain my_icloud_export.txt
   ```

3. Add homework or chores as tasks with optional due dates:

   ```bash
   python schedule_cli.py add-task "Chemistry homework" homework --due "2023-09-05 23:59"
   ```

4. Generate the schedule text file your front-end can read (defaults to the next 7 days
   starting today):

   ```bash
   python schedule_cli.py generate --output schedule_next_week.txt
   ```

The generated file groups events by day, includes recurring classes, imported calendar
entries, and tasks that have due dates within the window.

## Command reference

All commands accept `--data-file` if you want to keep multiple schedules. By default the
script reads and writes `data/events.json`.

### `add-recurring`

Adds a weekly recurring event (class, chore, standing meeting, etc.).

```
python schedule_cli.py add-recurring TITLE CATEGORY START_DATE START_TIME END_TIME DAYS \
    [--end-date YYYY-MM-DD] [--location TEXT] [--notes TEXT]
```

* `DAYS` is a comma-separated list such as `Mon,Wed,Fri` (names are matched by prefix).
* Use 24-hour times (e.g., `14:30` for 2:30 PM).

### `add-single`

Adds a single one-off event.

```
python schedule_cli.py add-single TITLE CATEGORY "YYYY-MM-DD HH:MM" "YYYY-MM-DD HH:MM" \
    [--location TEXT] [--notes TEXT]
```

### `add-task`

Adds an open task. Tasks show up in the generated schedule on their due date as an
all-day reminder.

```
python schedule_cli.py add-task TITLE CATEGORY [--due "YYYY-MM-DD HH:MM"] [--notes TEXT]
```

### `list`

Prints the currently stored recurring events, one-off events, and tasks.

```
python schedule_cli.py list
```

### `generate`

Expands every event into concrete occurrences and writes a plain-text agenda.

```
python schedule_cli.py generate [--start-date YYYY-MM-DD] [--days N] [--output PATH]
```

* `--start-date` defaults to today.
* `--days` defaults to 7, which gives you the next week.

## Importing from plain text

The `import-plain` command helps you move events from another calendar (for example,
an iCloud export you cleaned up in a text editor). The file should contain one event per
line using this pipe-separated format:

```
YYYY-MM-DD HH:MM-HH:MM | Title | Category | Location | Notes
```

Only the first two columns (date/time and title) are required. Empty optional columns can
be omitted or left blank. Example:

```
2023-09-04 15:00-16:00 | Dentist appointment | health | Downtown Clinic | Bring insurance card
2023-09-06 18:30-20:00 | Game night | social
```

Run the import like this:

```
python schedule_cli.py import-plain icloud_cleaned.txt
```

Every imported event is stored exactly once in `data/events.json` so you can keep the
file as your source of truth going forward.

## Automating updates

If you want Codex to make changes automatically based on chat commands, point it to the
`schedule_cli.py` script. For example, the front-end can write new commands (such as
`add-task` or `generate`) into your message box, and Codex can execute them to keep the
schedule current.

## Validating the install

To make sure the project runs on your machine, you can verify that all Python files
compile:

```
python -m compileall schedule schedule_cli.py
```

This command is also used in automated checks before changes are committed.
