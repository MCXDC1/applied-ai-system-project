from datetime import date, timedelta
from pawpal_system import Task, Pet, Owner, Scheduler, ScheduledItem, is_due_today


def test_mark_complete_changes_status():
    task = Task(description="Feed dog")
    assert task.is_completed is False
    task.complete()
    assert task.is_completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Buddy", species="Dog", age=3, breed="Labrador")
    assert len(pet.tasks) == 0
    pet.add_task(Task(description="Morning walk"))
    assert len(pet.tasks) == 1


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_owner(wake="07:00", sleep="22:00", pets=None):
    return Owner(name="Alex", wake_time=wake, sleep_time=sleep, pets=pets or [])


def make_pet(name="Buddy"):
    return Pet(name=name, species="Dog", age=3, breed="Labrador")


def test_single_daily_task_appears_in_schedule():
    pet = make_pet()
    pet.add_task(Task(description="Walk", frequency="daily"))
    owner = make_owner(pets=[pet])
    scheduler = Scheduler(owner)
    schedule = scheduler.build_schedule(reference_date=date.today())
    assert len(schedule) == 1
    assert schedule[0].task.description == "Walk"


def test_task_with_explicit_time_is_pinned():
    pet = make_pet()
    pet.add_task(Task(description="Meds", frequency="daily", time="09:00"))
    owner = make_owner(wake="07:00", pets=[pet])
    scheduler = Scheduler(owner)
    schedule = scheduler.build_schedule(reference_date=date.today())
    assert schedule[0].time_slot == "09:00"


def test_task_without_time_defaults_to_wake_time():
    pet = make_pet()
    pet.add_task(Task(description="Breakfast", frequency="daily"))
    owner = make_owner(wake="07:00", pets=[pet])
    scheduler = Scheduler(owner)
    schedule = scheduler.build_schedule(reference_date=date.today())
    assert schedule[0].time_slot == "07:00"


def test_two_tasks_sorted_chronologically():
    pet = make_pet()
    pet.add_task(Task(description="Late walk", frequency="daily", time="18:00"))
    pet.add_task(Task(description="Morning meds", frequency="daily", time="08:00"))
    owner = make_owner(pets=[pet])
    scheduler = Scheduler(owner)
    schedule = scheduler.build_schedule(reference_date=date.today())
    assert schedule[0].task.description == "Morning meds"
    assert schedule[1].task.description == "Late walk"


def test_same_time_sorted_by_priority():
    pet = make_pet()
    pet.add_task(Task(description="Low priority", frequency="daily", time="08:00", priority=3))
    pet.add_task(Task(description="High priority", frequency="daily", time="08:00", priority=1))
    owner = make_owner(pets=[pet])
    scheduler = Scheduler(owner)
    schedule = scheduler.build_schedule(reference_date=date.today())
    assert schedule[0].task.description == "High priority"
    assert schedule[1].task.description == "Low priority"


def test_complete_daily_task_creates_next_day_task():
    today = date.today()
    pet = make_pet()
    task = Task(description="Walk", frequency="daily", due_date=today)
    pet.add_task(task)
    owner = make_owner(pets=[pet])
    scheduler = Scheduler(owner)
    schedule = scheduler.build_schedule(reference_date=today)
    next_task = scheduler.complete_task(schedule[0])
    assert next_task is not None
    assert next_task.due_date == today + timedelta(days=1)


def test_complete_weekly_task_creates_next_week_task():
    monday = date(2026, 3, 30)  # a known Monday
    pet = make_pet()
    task = Task(description="Bath", frequency="weekly", due_date=monday)
    pet.add_task(task)
    owner = make_owner(pets=[pet])
    scheduler = Scheduler(owner)
    schedule = scheduler.build_schedule(reference_date=monday)
    next_task = scheduler.complete_task(schedule[0])
    assert next_task is not None
    assert next_task.due_date == monday + timedelta(weeks=1)


def test_owner_with_two_pets_returns_all_tasks():
    pet1 = make_pet("Buddy")
    pet1.add_task(Task(description="Walk"))
    pet2 = make_pet("Whiskers")
    pet2.add_task(Task(description="Feed cat"))
    owner = make_owner(pets=[pet1, pet2])
    assert len(owner.get_all_tasks()) == 2


# ---------------------------------------------------------------------------
# Edge cases: pet / task state
# ---------------------------------------------------------------------------

def test_pet_with_no_tasks_builds_empty_schedule():
    pet = make_pet()
    owner = make_owner(pets=[pet])
    scheduler = Scheduler(owner)
    schedule = scheduler.build_schedule(reference_date=date.today())
    assert schedule == []


def test_all_tasks_completed_builds_empty_schedule():
    pet = make_pet()
    task = Task(description="Walk", frequency="daily")
    task.is_completed = True
    pet.add_task(task)
    owner = make_owner(pets=[pet])
    scheduler = Scheduler(owner)
    schedule = scheduler.build_schedule(reference_date=date.today())
    assert schedule == []


def test_complete_monthly_task_returns_none():
    pet = make_pet()
    task = Task(description="Vet visit", frequency="monthly", due_date=date(2026, 4, 1))
    pet.add_task(task)
    owner = make_owner(pets=[pet])
    scheduler = Scheduler(owner)
    schedule = scheduler.build_schedule(reference_date=date(2026, 4, 1))
    next_task = scheduler.complete_task(schedule[0])
    assert next_task is None


def test_complete_yearly_task_returns_none():
    pet = make_pet()
    task = Task(description="Annual checkup", frequency="yearly", due_date=date(2026, 1, 1))
    pet.add_task(task)
    owner = make_owner(pets=[pet])
    scheduler = Scheduler(owner)
    schedule = scheduler.build_schedule(reference_date=date(2026, 1, 1))
    next_task = scheduler.complete_task(schedule[0])
    assert next_task is None


# ---------------------------------------------------------------------------
# Edge cases: scheduling conflicts
# ---------------------------------------------------------------------------

def test_warn_same_time_conflicts_same_pet():
    pet = make_pet()
    pet.add_task(Task(description="Walk", frequency="daily", time="08:00"))
    pet.add_task(Task(description="Meds", frequency="daily", time="08:00"))
    owner = make_owner(pets=[pet])
    scheduler = Scheduler(owner)
    scheduler.build_schedule(reference_date=date.today())
    warning = scheduler.warn_same_time_conflicts()
    assert "WARNING" in warning


def test_warn_same_time_conflicts_different_pets():
    pet1 = make_pet("Buddy")
    pet1.add_task(Task(description="Walk", frequency="daily", time="08:00"))
    pet2 = make_pet("Whiskers")
    pet2.add_task(Task(description="Feed cat", frequency="daily", time="08:00"))
    owner = make_owner(pets=[pet1, pet2])
    scheduler = Scheduler(owner)
    scheduler.build_schedule(reference_date=date.today())
    warning = scheduler.warn_same_time_conflicts()
    assert "WARNING" in warning


def test_no_conflict_returns_empty_string():
    pet = make_pet()
    pet.add_task(Task(description="Walk", frequency="daily", time="08:00"))
    pet.add_task(Task(description="Meds", frequency="daily", time="09:00"))
    owner = make_owner(pets=[pet])
    scheduler = Scheduler(owner)
    scheduler.build_schedule(reference_date=date.today())
    assert scheduler.warn_same_time_conflicts() == ""


def test_detect_conflicts_overlapping_windows():
    pet = make_pet()
    # Walk starts 08:00, duration 1:00 -> ends 09:00
    # Meds starts 08:30 -> overlap
    pet.add_task(Task(description="Walk", frequency="daily", time="08:00", duration="1:00"))
    pet.add_task(Task(description="Meds", frequency="daily", time="08:30"))
    owner = make_owner(pets=[pet])
    scheduler = Scheduler(owner)
    scheduler.build_schedule(reference_date=date.today())
    conflicts = scheduler.detect_conflicts()
    assert len(conflicts) == 1


def test_detect_conflicts_misses_non_adjacent_overlap():
    """
    Known limitation: detect_conflicts only checks adjacent pairs.
    Three tasks A(08:00, 2h), B(08:30, 10min), C(09:00) — A overlaps C
    but the check only compares (A,B) and (B,C), so (A,C) is missed.
    This test documents that bug; it is expected to FAIL until fixed.
    """
    pet = make_pet()
    pet.add_task(Task(description="A", frequency="daily", time="08:00", duration="2:00"))
    pet.add_task(Task(description="B", frequency="daily", time="08:30", duration="0:10"))
    pet.add_task(Task(description="C", frequency="daily", time="09:00"))
    owner = make_owner(pets=[pet])
    scheduler = Scheduler(owner)
    scheduler.build_schedule(reference_date=date.today())
    conflicts = scheduler.detect_conflicts()
    pairs = [(a.task.description, b.task.description) for a, b in conflicts]
    assert ("A", "C") in pairs  # currently fails — bug in detect_conflicts


# ---------------------------------------------------------------------------
# Edge cases: recurring task scheduling
# ---------------------------------------------------------------------------

def test_weekly_task_not_due_on_non_monday():
    tuesday = date(2026, 3, 31)
    assert tuesday.weekday() == 1  # sanity check
    task = Task(description="Bath", frequency="weekly")
    assert is_due_today(task, reference_date=tuesday) is False


def test_weekly_task_due_on_monday():
    monday = date(2026, 3, 30)
    assert monday.weekday() == 0  # sanity check
    task = Task(description="Bath", frequency="weekly")
    assert is_due_today(task, reference_date=monday) is True


def test_due_date_overrides_frequency():
    specific_date = date(2026, 4, 7)  # a Tuesday
    task = Task(description="Vet", frequency="weekly", due_date=specific_date)
    assert is_due_today(task, reference_date=specific_date) is True
    assert is_due_today(task, reference_date=specific_date + timedelta(days=7)) is False


def test_complete_task_auto_adds_to_pet_list():
    today = date.today()
    pet = make_pet()
    task = Task(description="Walk", frequency="daily", due_date=today)
    pet.add_task(task)
    owner = make_owner(pets=[pet])
    scheduler = Scheduler(owner)
    schedule = scheduler.build_schedule(reference_date=today)
    initial_count = len(pet.tasks)
    scheduler.complete_task(schedule[0])
    assert len(pet.tasks) == initial_count + 1
    assert pet.tasks[-1].due_date == today + timedelta(days=1)


def test_complete_already_completed_task():
    """Completing a task twice: is_completed stays True and another next task is returned."""
    today = date.today()
    task = Task(description="Walk", frequency="daily", due_date=today)
    task.complete()
    assert task.is_completed is True
    next_task = task.complete()  # second call
    assert task.is_completed is True
    assert next_task is not None  # still produces a next occurrence


# ---------------------------------------------------------------------------
# Edge cases: sorting behavior
# ---------------------------------------------------------------------------

def test_sort_by_time_task_without_time_sorts_to_zero():
    """Tasks with no time sort to minute 0 (midnight) in sort_by_time."""
    pet = make_pet()
    t_no_time = Task(description="No time", frequency="daily")
    t_timed = Task(description="Timed", frequency="daily", time="06:00")
    owner = make_owner(pets=[pet])
    scheduler = Scheduler(owner)
    sorted_tasks = scheduler.sort_by_time([t_timed, t_no_time])
    assert sorted_tasks[0].description == "No time"  # 0 < 360


def test_build_schedule_vs_sort_by_time_timeless_task_placement():
    """
    Timeless tasks get wake_time in build_schedule but minute 0 in sort_by_time.
    This test documents the inconsistency.
    """
    pet = make_pet()
    pet.add_task(Task(description="No time task", frequency="daily"))
    owner = make_owner(wake="07:00", pets=[pet])
    scheduler = Scheduler(owner)
    schedule = scheduler.build_schedule(reference_date=date.today())
    # In build_schedule, timeless tasks use wake_time
    assert schedule[0].time_slot == "07:00"
    # In sort_by_time, the same task would be treated as minute 0
    sorted_tasks = scheduler.sort_by_time([schedule[0].task])
    from pawpal_system import _time_to_minutes
    key = _time_to_minutes(sorted_tasks[0].time) if sorted_tasks[0].time else 0
    assert key == 0


# ---------------------------------------------------------------------------
# Edge cases: filtering
# ---------------------------------------------------------------------------

def test_filter_tasks_unknown_pet_returns_empty():
    pet = make_pet("Buddy")
    pet.add_task(Task(description="Walk"))
    owner = make_owner(pets=[pet])
    scheduler = Scheduler(owner)
    result = scheduler.filter_tasks(pet_name="Ghost")
    assert result == []


def test_filter_schedule_before_build_returns_empty():
    owner = make_owner(pets=[make_pet()])
    scheduler = Scheduler(owner)
    # No build_schedule() called
    result = scheduler.filter_schedule(pet_name="Buddy")
    assert result == []


def test_explain_schedule_before_build_returns_message():
    owner = make_owner(pets=[make_pet()])
    scheduler = Scheduler(owner)
    msg = scheduler.explain_schedule()
    assert "build_schedule" in msg
