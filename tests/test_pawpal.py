from datetime import date, timedelta
from pawpal_system import Task, Pet, Owner


def make_owner(wake="07:00", sleep="22:00", pets=None):
    return Owner(name="Alex", wake_time=wake, sleep_time=sleep, pets=pets or [])


def make_pet(name="Buddy"):
    return Pet(name=name, species="Dog", age=3, breed="Labrador")


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

def test_mark_complete_changes_status():
    task = Task(description="Feed dog")
    assert task.is_completed is False
    task.complete()
    assert task.is_completed is True


def test_complete_daily_task_returns_next_day():
    today = date.today()
    task = Task(description="Walk", frequency="daily", due_date=today)
    next_task = task.complete()
    assert next_task is not None
    assert next_task.due_date == today + timedelta(days=1)


def test_complete_weekly_task_returns_next_week():
    monday = date(2026, 3, 30)
    task = Task(description="Bath", frequency="weekly", due_date=monday)
    next_task = task.complete()
    assert next_task is not None
    assert next_task.due_date == monday + timedelta(weeks=1)


def test_complete_monthly_task_returns_none():
    task = Task(description="Vet visit", frequency="monthly", due_date=date(2026, 4, 1))
    assert task.complete() is None


def test_complete_yearly_task_returns_none():
    task = Task(description="Annual checkup", frequency="yearly", due_date=date(2026, 1, 1))
    assert task.complete() is None


def test_complete_already_completed_task():
    today = date.today()
    task = Task(description="Walk", frequency="daily", due_date=today)
    task.complete()
    assert task.is_completed is True
    next_task = task.complete()
    assert task.is_completed is True
    assert next_task is not None


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

def test_add_task_increases_pet_task_count():
    pet = make_pet()
    assert len(pet.tasks) == 0
    pet.add_task(Task(description="Morning walk"))
    assert len(pet.tasks) == 1


def test_remove_task_decreases_pet_task_count():
    pet = make_pet()
    pet.add_task(Task(description="Walk"))
    pet.remove_task("Walk")
    assert len(pet.tasks) == 0


def test_get_pending_tasks_excludes_completed():
    pet = make_pet()
    t1 = Task(description="Walk")
    t2 = Task(description="Feed")
    t2.is_completed = True
    pet.add_task(t1)
    pet.add_task(t2)
    assert len(pet.get_pending_tasks()) == 1
    assert pet.get_pending_tasks()[0].description == "Walk"


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

def test_owner_with_two_pets_returns_all_tasks():
    pet1 = make_pet("Buddy")
    pet1.add_task(Task(description="Walk"))
    pet2 = make_pet("Whiskers")
    pet2.add_task(Task(description="Feed cat"))
    owner = make_owner(pets=[pet1, pet2])
    assert len(owner.get_all_tasks()) == 2


def test_owner_get_availability_returns_wake_sleep():
    owner = make_owner(wake="08:00", sleep="21:00")
    wake, sleep = owner.get_availability()
    assert wake == "08:00"
    assert sleep == "21:00"
