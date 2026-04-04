from pawpal_system import Task, Pet


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
