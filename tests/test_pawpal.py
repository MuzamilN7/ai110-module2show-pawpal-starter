from datetime import datetime

from pawpal_system import Pet, Task


def test_mark_complete_sets_completed():
    task = Task("Morning walk", datetime(2026, 1, 1, 7, 30))

    task.mark_complete()

    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Buddy", species="Dog")
    assert len(pet.tasks) == 0

    pet.add_task(Task("Feeding", datetime(2026, 1, 1, 8, 0)))

    assert len(pet.tasks) == 1
