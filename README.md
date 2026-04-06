# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## Features

- **Sorting by time** — `build_schedule()` converts every `"HH:MM"` string to total minutes so tasks are ordered correctly across midnight boundaries, then breaks ties by priority (1=high, 2=medium, 3=low).
- **Priority-based ordering** — tasks with priority 1 always appear before lower-priority tasks that share the same time slot, ensuring the most important care happens first.
- **Daily/weekly recurrence** — when `complete_task()` is called, it auto-generates the next occurrence of the task (`today + 1 day` for daily, `today + 7 days` for weekly) and attaches it to the pet, so recurring care never falls off the schedule.
- **Frequency filtering** — `is_due_today()` checks each task's `due_date` and `frequency` so only relevant tasks appear in a given day's schedule; monthly/yearly tasks are excluded unless their date matches.
- **Conflict warnings** — `warn_same_time_conflicts()` scans the schedule for tasks pinned to the exact same time slot and reports every conflicting pair, even across different pets.
- **Overlap detection** — `detect_conflicts()` goes further by comparing time *windows*: tasks without an explicit duration get a 30-minute default block, and any pair whose windows overlap is flagged in `explain_schedule()`.
- **Multi-pet support** — an `Owner` holds a list of pets; all scheduling, filtering, and conflict checks work across the full roster in a single pass.
- **Task filtering** — `filter_tasks()` and `filter_schedule()` let you slice the schedule by pet name, completion status, or both, supporting targeted views in the UI.
- **Human-readable output** — `explain_schedule()` formats the daily plan as a bordered table with frequency, priority label, and pet name per row, and appends any detected overlaps at the bottom.

### Smarter Scheduling

The scheduler is able to place tasks into an Owner's schedule and seperate tasks based on pet, priority, and frequency. It is able to update tasks that have been completed to the next needed occurence. It is able to detect conflicts between timing. It is able to remember the Owner and Pet for easy updating. 

### Testing PawPal+

python -m pytest

The tests cover that tasks are being added in relation to the info that is put in by the user. It makes sure that there are not duplicate events. It makes sure that daily/weekly/etc. tasks are being updated based on freuency. It tests edge cases such as Owners with no tasks for the Pet and the schedule being built. It tests that tasks get automatically sorted to midnight or waketime if the user does not put the information in.

My confidence is a 4. I believe the system is working as intended but believe that I will find minor tweaks once I move around within the application.
