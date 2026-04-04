from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Task:
    description: str
    frequency: str = "daily"  # "daily", "weekly", "monthly", "yearly"
    time: str = ""            # "HH:MM" format
    is_completed: bool = False

    def complete(self) -> None:
        """Marks this task as completed."""
        self.is_completed = True

    def to_dict(self) -> dict:
        """Returns a dictionary representation of the task."""
        return {
            "description": self.description,
            "time": self.time,
            "frequency": self.frequency,
            "is_completed": self.is_completed,
        }


@dataclass
class ScheduledItem:
    task: Task
    time_slot: str


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

    def get_availability(self) -> tuple[str, str]:
        """Returns the owner's wake and sleep times as a (wake, sleep) tuple."""
        return (self.wake_time, self.sleep_time)

    def get_all_tasks(self) -> list[Task]:
        """Returns all pending tasks across every pet."""
        tasks = []
        for pet in self.pets:
            tasks.extend(pet.get_pending_tasks())
        return tasks

    def get_tasks_for_pet(self, pet_name: str) -> list[Task]:
        """Returns all pending tasks for the pet with the given name."""
        for pet in self.pets:
            if pet.name == pet_name:
                return pet.get_pending_tasks()
        return []


class Scheduler:
    def __init__(self, owner: Owner):
        self.owner = owner
        self.pets = owner.pets
        self.schedule: list[ScheduledItem] = []

    def build_schedule(self) -> list[ScheduledItem]:
        """
        Assigns each pending task a time slot within the owner's wake/sleep window.
        Tasks with a time are pinned to that slot; the rest default to wake_time.
        """
        wake_time, _ = self.owner.get_availability()
        all_tasks = self.owner.get_all_tasks()

        self.schedule = []
        for task in all_tasks:
            if task.frequency != "daily":
                continue
            time_slot = task.time if task.time else wake_time
            self.schedule.append(ScheduledItem(task=task, time_slot=time_slot))

        return self.schedule

    def explain_schedule(self) -> str:
        """Returns a formatted, human-readable string of the current daily schedule."""
        if not self.schedule:
            return "No schedule built yet. Call build_schedule() first."

        sorted_items = sorted(self.schedule, key=lambda x: x.time_slot)

        title = f"Daily Schedule for {self.owner.name}"
        border = "=" * (len(title) + 4)
        lines = [border, f"  {title}  ", border, ""]

        for item in sorted_items:
            freq = item.task.frequency.replace("_", " ")
            lines.append(f"  {item.time_slot}  |  {item.task.description:<25}  [{freq}]")

        lines.append("")
        lines.append(border)
        return "\n".join(lines)




