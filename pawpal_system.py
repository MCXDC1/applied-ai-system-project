from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Pet:
    name: str
    species: str
    age: int
    breed: str
    dietary_restrictions: list[str] = field(default_factory=list)
    medication_information: list[str] = field(default_factory=list)
    additional_information: list[str] = field(default_factory=list)

    def get_info(self) -> str:
        pass


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str  # "low", "medium", "high"
    preferred_time: str = ""
    is_completed: bool = False

    def complete(self) -> None:
        pass

    def to_dict(self) -> dict:
        pass


class TaskManager:
    def __init__(self):
        self.tasks: list[Task] = []

    def add_task(self, task: Task) -> None:
        pass

    def remove_task(self, title: str) -> None:
        pass

    def update_task(self, title: str, **kwargs) -> None:
        pass

    def get_by_priority(self, priority: str) -> list[Task]:
        pass

    def get_all_tasks(self) -> list[Task]:
        pass


class Owner:
    def __init__(self, name: str, wake_time: str, sleep_time: str, pet: Pet,
                 preferences: Optional[list[str]] = None,
                 additional_information: Optional[list[str]] = None):
        self.name = name
        self.wake_time = wake_time
        self.sleep_time = sleep_time
        self.pet = pet
        self.preferences: list[str] = preferences or []
        self.additional_information: list[str] = additional_information or []

    def get_availability(self) -> tuple:
        pass


class Scheduler:
    def __init__(self, owner: Owner, task_manager: TaskManager):
        self.owner = owner
        self.pet = owner.pet
        self.task_manager = task_manager
        self.schedule: list[dict] = []

    def build_schedule(self) -> list[dict]:
        pass

    def explain_schedule(self) -> str:
        pass

    def get_total_time(self) -> int:
        pass
