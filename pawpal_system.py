from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional



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

    @classmethod
    def from_dict(cls, d: dict) -> "Task":
        return cls(
            description=d["description"],
            frequency=d.get("frequency", "daily"),
            duration=d.get("duration", ""),
            priority=d.get("priority", 2),
            time=d.get("time", ""),
            is_completed=d.get("is_completed", False),
            due_date=date.fromisoformat(d["due_date"]) if d.get("due_date") else None,
        )



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

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "species": self.species,
            "age": self.age,
            "breed": self.breed,
            "dietary_restrictions": self.dietary_restrictions,
            "medication_information": self.medication_information,
            "additional_information": self.additional_information,
            "tasks": [t.to_dict() for t in self.tasks],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Pet":
        pet = cls(
            name=d["name"],
            species=d["species"],
            age=d["age"],
            breed=d["breed"],
            dietary_restrictions=d.get("dietary_restrictions", []),
            medication_information=d.get("medication_information", []),
            additional_information=d.get("additional_information", []),
        )
        pet.tasks = [Task.from_dict(t) for t in d.get("tasks", [])]
        return pet


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
