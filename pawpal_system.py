from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional


def _time_to_minutes(time_str: str) -> int:
    """Converts 'HH:MM' to total minutes since midnight for correct numeric sorting."""
    h, m = map(int, time_str.split(":"))
    return h * 60 + m


def is_due_today(task: "Task", reference_date: date = None) -> bool:
    """Returns True if a task should appear in today's schedule based on its frequency."""
    if reference_date is None:
        reference_date = date.today()
    # If a specific due date was assigned (e.g. for a rescheduled recurring task), use it.
    if task.due_date is not None:
        return task.due_date == reference_date
    if task.frequency == "daily":
        return True
    if task.frequency == "weekly":
        return reference_date.weekday() == 0  # every Monday
    if task.frequency == "monthly":
        return reference_date.day == 1
    if task.frequency == "yearly":
        return reference_date.month == 1 and reference_date.day == 1
    return False


@dataclass
class Task:
    description: str
    frequency: str = "daily"         # "daily", "weekly", "monthly", "yearly"
    duration: str = ""               # "H:MM" format, e.g. "1:30" for 1 hour 30 minutes
    priority: int = 2                # 1=high, 2=medium, 3=low
    time: str = ""                   # "HH:MM" format
    is_completed: bool = False
    due_date: Optional[date] = None  # set for rescheduled recurring tasks

    def complete(self) -> Optional["Task"]:
        """Marks this task as completed.

        For 'daily' and 'weekly' tasks, returns a new Task instance scheduled
        for the next occurrence (today + 1 day or today + 7 days respectively).
        Returns None for non-recurring frequencies.
        """
        self.is_completed = True
        base = self.due_date or date.today()
        if self.frequency == "daily":
            next_date = base + timedelta(days=1)
        elif self.frequency == "weekly":
            next_date = base + timedelta(weeks=1)
        else:
            return None
        return Task(
            description=self.description,
            frequency=self.frequency,
            duration=self.duration,
            priority=self.priority,
            time=self.time,
            due_date=next_date,
        )

    def to_dict(self) -> dict:
        """Returns a dictionary representation of the task."""
        return {
            "description": self.description,
            "time": self.time,
            "duration": self.duration,
            "frequency": self.frequency,
            "priority": self.priority,
            "is_completed": self.is_completed,
            "due_date": self.due_date.isoformat() if self.due_date else None,
        }


@dataclass
class ScheduledItem:
    task: Task
    time_slot: str
    pet: "Pet" = field(default=None)

    def end_minutes(self) -> int:
        """Returns the minute-of-day when this item ends, defaulting to a 30-min block."""
        start = _time_to_minutes(self.time_slot)
        if self.task.duration:
            h, m = map(int, self.task.duration.split(":"))
            return start + h * 60 + m
        return start + 30


@dataclass
class Pet:
    name: str
    species: str
    age: int
    breed: str
    dietary_restrictions: list[str] = field(default_factory=list)
    medication_information: list[str] = field(default_factory=list)
    additional_information: list[str] = field(default_factory=list)
    tasks: list[Task] = field(default_factory=list)

    def get_info(self) -> str:
        """Returns a formatted string summary of the pet's profile."""
        lines = [
            f"Name: {self.name}",
            f"Species: {self.species} | Breed: {self.breed} | Age: {self.age}",
        ]
        if self.dietary_restrictions:
            lines.append(f"Diet: {', '.join(self.dietary_restrictions)}")
        if self.medication_information:
            lines.append(f"Medications: {', '.join(self.medication_information)}")
        if self.additional_information:
            lines.append(f"Notes: {', '.join(self.additional_information)}")
        return "\n".join(lines)

    def add_task(self, task: Task) -> None:
        """Appends a task to the pet's task list."""
        self.tasks.append(task)

    def remove_task(self, description: str) -> None:
        """Removes all tasks matching the given description from the pet's task list."""
        self.tasks = [t for t in self.tasks if t.description != description]

    def get_pending_tasks(self) -> list[Task]:
        """Returns all incomplete tasks for this pet."""
        return [t for t in self.tasks if not t.is_completed]


class Owner:
    def __init__(self, name: str, wake_time: str, sleep_time: str, pets: list[Pet],
                 preferences: Optional[list[str]] = None,
                 additional_information: Optional[list[str]] = None):
        self.name = name
        self.wake_time = wake_time      # "HH:MM" format
        self.sleep_time = sleep_time    # "HH:MM" format
        self.pets = pets
        self.preferences: list[str] = preferences or []
        self.additional_information: list[str] = additional_information or []

    def add_pet(self, pet: "Pet") -> None:
        """Adds a new pet to the owner's pet list."""
        self.pets.append(pet)

    def get_availability(self) -> tuple[str, str]:
        """Returns the owner's wake and sleep times as a (wake, sleep) tuple."""
        return (self.wake_time, self.sleep_time)

    def get_all_tasks(self) -> list[Task]:
        """Returns all pending tasks across every pet."""
        tasks = []
        for pet in self.pets:
            tasks.extend(pet.get_pending_tasks())
        return tasks

    def get_tasks_for_pet(self, pet_name: str, completed: bool = False) -> list[Task]:
        """Returns tasks for the named pet, filtered by completion status."""
        for pet in self.pets:
            if pet.name == pet_name:
                return [t for t in pet.tasks if t.is_completed == completed]
        return []

    def get_tasks_by_status(self, completed: bool) -> list[Task]:
        """Returns all tasks across every pet filtered by completion status."""
        return [t for pet in self.pets for t in pet.tasks if t.is_completed == completed]


class Scheduler:
    def __init__(self, owner: Owner):
        self.owner = owner
        self.pets = owner.pets
        self.schedule: list[ScheduledItem] = []

    def build_schedule(self, reference_date: date = None) -> list[ScheduledItem]:
        """
        Assigns each due task a time slot within the owner's wake/sleep window.
        Tasks with a time are pinned to that slot; the rest default to wake_time.
        Tasks are sorted by time then priority (1=highest).
        """
        if reference_date is None:
            reference_date = date.today()

        wake_time, _ = self.owner.get_availability()
        self.schedule = []

        for pet in self.owner.pets:
            for task in pet.get_pending_tasks():
                if not is_due_today(task, reference_date):
                    continue
                time_slot = task.time if task.time else wake_time
                self.schedule.append(ScheduledItem(task=task, time_slot=time_slot, pet=pet))

        # Sort by time, then by priority within the same slot
        self.schedule.sort(key=lambda x: (_time_to_minutes(x.time_slot), x.task.priority))
        return self.schedule

    def complete_task(self, item: ScheduledItem) -> Optional[Task]:
        """Marks a scheduled task complete and auto-schedules the next occurrence.

        """
        next_task = item.task.complete()
        if next_task is not None and item.pet is not None:
            item.pet.add_task(next_task)
        return next_task

    def filter_tasks(self, pet_name: str = None, completed: bool = None) -> list[Task]:
        """
        Returns Task objects filtered by pet name, completion status, or both.

        """
        results = []
        for pet in self.owner.pets:
            if pet_name is not None and pet.name != pet_name:
                continue
            for task in pet.tasks:
                if completed is not None and task.is_completed != completed:
                    continue
                results.append(task)
        return results

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Returns tasks sorted chronologically using a lambda key that converts 'HH:MM' to minutes."""
        return sorted(
            tasks,
            key=lambda task: _time_to_minutes(task.time) if task.time else 0,
        )

    def filter_schedule(self, pet_name: str = None, completed: bool = None) -> list[ScheduledItem]:
        """Returns a filtered view of the schedule by pet name and/or completion status."""
        items = self.schedule
        if pet_name is not None:
            items = [i for i in items if i.pet and i.pet.name == pet_name]
        if completed is not None:
            items = [i for i in items if i.task.is_completed == completed]
        return items

    def warn_same_time_conflicts(self) -> str:
        """Returns a warning string listing every pair of tasks
        (same pet or different pets) that share the exact same time slot.
        Returns an empty string if no conflicts are found.
        """
        # Group items by time slot
        from collections import defaultdict
        slots: dict[str, list[ScheduledItem]] = defaultdict(list)
        for item in self.schedule:
            slots[item.time_slot].append(item)

        warnings = []
        for time_slot, items in slots.items():
            if len(items) < 2:
                continue
            for i in range(len(items)):
                for j in range(i + 1, len(items)):
                    a, b = items[i], items[j]
                    pet_a = a.pet.name if a.pet else "?"
                    pet_b = b.pet.name if b.pet else "?"
                    warnings.append(
                        f"  WARNING {time_slot}: '{a.task.description}' ({pet_a})"
                        f" conflicts with '{b.task.description}' ({pet_b})"
                    )

        if not warnings:
            return ""
        return "Scheduling conflicts detected:\n" + "\n".join(warnings)

    def detect_conflicts(self) -> list[tuple[ScheduledItem, ScheduledItem]]:
        """
        Returns pairs of ScheduledItems whose time windows overlap.
        Assumes a 30-minute default block for tasks without a duration.
        """
        sorted_items = sorted(self.schedule, key=lambda x: _time_to_minutes(x.time_slot))
        conflicts = []
        for i in range(len(sorted_items) - 1):
            a, b = sorted_items[i], sorted_items[i + 1]
            if a.end_minutes() > _time_to_minutes(b.time_slot):
                conflicts.append((a, b))
        return conflicts

    def explain_schedule(self) -> str:
        """Returns a formatted, human-readable string of the current daily schedule."""
        if not self.schedule:
            return "No schedule built yet. Call build_schedule() first."

        title = f"Daily Schedule for {self.owner.name}"
        border = "=" * (len(title) + 4)
        lines = [border, f"  {title}  ", border, ""]

        priority_label = {1: "HIGH", 2: "MED", 3: "LOW"}
        for item in self.schedule:
            freq = item.task.frequency.replace("_", " ")
            pet_name = item.pet.name if item.pet else "?"
            pri = priority_label.get(item.task.priority, str(item.task.priority))
            lines.append(
                f"  {item.time_slot}  |  {item.task.description:<25}  "
                f"[{freq}] [{pri}] ({pet_name})"
            )

        conflicts = self.detect_conflicts()
        if conflicts:
            lines.append("")
            lines.append("  ⚠ CONFLICTS DETECTED:")
            for a, b in conflicts:
                lines.append(
                    f"    '{a.task.description}' ({a.time_slot}) overlaps "
                    f"'{b.task.description}' ({b.time_slot})"
                )

        lines.append("")
        lines.append(border)
        return "\n".join(lines)
