from datetime import datetime, timedelta

from pawpal_system import Owner, Pet, Scheduler, Task

# Far-future base so recurrence math is deterministic (never "overdue").
FUTURE = datetime(2099, 1, 1)


def at(hour: int, minute: int = 0, day: int = 1) -> datetime:
    return FUTURE.replace(day=day, hour=hour, minute=minute)


def make_scheduler(*pets: Pet) -> Scheduler:
    owner = Owner(name="Test Owner")
    for pet in pets:
        owner.add_pet(pet)
    return Scheduler(owner)


def test_mark_complete_sets_completed():
    task = Task("Morning walk", datetime(2026, 1, 1, 7, 30))

    task.mark_complete()

    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Buddy", species="Dog")
    assert len(pet.tasks) == 0

    pet.add_task(Task("Feeding", datetime(2026, 1, 1, 8, 0)))

    assert len(pet.tasks) == 1


# --- Sorting correctness ---------------------------------------------------

def test_sort_by_time_returns_chronological_order_across_pets():
    buddy = Pet("Buddy", "Dog")
    whiskers = Pet("Whiskers", "Cat")
    # Added deliberately out of order, split across two pets.
    buddy.add_task(Task("Evening walk", at(18)))
    buddy.add_task(Task("Morning walk", at(7, 30)))
    whiskers.add_task(Task("Breakfast", at(8)))
    whiskers.add_task(Task("Brush fur", at(19, 30)))

    result = make_scheduler(buddy, whiskers).sort_by_time()

    assert [t.description for t in result] == [
        "Morning walk", "Breakfast", "Evening walk", "Brush fur",
    ]


def test_sort_by_time_orders_by_date_before_time_of_day():
    pet = Pet("Buddy", "Dog")
    pet.add_task(Task("Tomorrow early", at(7, day=2)))
    pet.add_task(Task("Today late", at(18, day=1)))

    result = make_scheduler(pet).sort_by_time()

    assert [t.description for t in result] == ["Today late", "Tomorrow early"]


def test_sort_by_time_does_not_mutate_pet_task_list():
    pet = Pet("Buddy", "Dog")
    pet.add_task(Task("Late", at(18)))
    pet.add_task(Task("Early", at(7)))

    make_scheduler(pet).sort_by_time()

    assert [t.description for t in pet.tasks] == ["Late", "Early"]


def test_sort_with_no_tasks_returns_empty_list():
    assert make_scheduler(Pet("Buddy", "Dog")).sort_by_time() == []
    assert make_scheduler().sort_by_time() == []


# --- Recurrence logic ------------------------------------------------------

def test_completing_daily_task_creates_task_for_next_day():
    pet = Pet("Buddy", "Dog")
    task = Task("Morning walk", at(7, 30), frequency="daily")
    pet.add_task(task)

    make_scheduler(pet).complete_task(pet, task)

    assert task.completed is True
    assert len(pet.tasks) == 2
    next_task = pet.tasks[1]
    assert next_task.time == task.time + timedelta(days=1)
    assert next_task.description == "Morning walk"
    assert next_task.frequency == "daily"
    assert next_task.completed is False


def test_completing_weekly_task_creates_task_one_week_later():
    task = Task("Brush fur", at(19, 30), frequency="weekly")

    next_task = task.mark_complete()

    assert next_task is not None
    assert next_task.time == task.time + timedelta(weeks=1)


def test_completing_one_time_task_creates_no_follow_up():
    pet = Pet("Buddy", "Dog")
    task = Task("Vet visit", at(9))
    pet.add_task(task)

    make_scheduler(pet).complete_task(pet, task)

    assert len(pet.tasks) == 1


def test_completing_same_task_twice_does_not_duplicate_recurrence():
    pet = Pet("Buddy", "Dog")
    task = Task("Morning walk", at(7, 30), frequency="daily")
    pet.add_task(task)
    scheduler = make_scheduler(pet)

    scheduler.complete_task(pet, task)
    scheduler.complete_task(pet, task)

    assert len(pet.tasks) == 2


def test_daily_recurrence_rolls_over_month_and_year():
    task = Task("Late feed", datetime(2099, 12, 31, 21, 0), frequency="daily")

    next_task = task.mark_complete()

    assert next_task.time == datetime(2100, 1, 1, 21, 0)


def test_overdue_recurring_task_skips_to_a_future_slot_at_same_time_of_day():
    task = Task("Morning walk", datetime(2000, 1, 1, 7, 30), frequency="daily")

    next_task = task.mark_complete()

    assert next_task.time > datetime.now()
    assert next_task.time - datetime.now() <= timedelta(days=1)
    assert (next_task.time.hour, next_task.time.minute) == (7, 30)


# --- Conflict detection ----------------------------------------------------

def test_conflict_warnings_flag_same_pet_duplicate_time():
    pet = Pet("Buddy", "Dog")
    pet.add_task(Task("Morning walk", at(7, 30)))
    pet.add_task(Task("Grooming", at(7, 30)))

    warnings = make_scheduler(pet).conflict_warnings()

    assert len(warnings) == 1
    assert "same pet" in warnings[0]
    assert "Morning walk" in warnings[0] and "Grooming" in warnings[0]


def test_conflict_warnings_flag_duplicate_time_across_pets():
    buddy = Pet("Buddy", "Dog")
    whiskers = Pet("Whiskers", "Cat")
    buddy.add_task(Task("Give medication", at(8)))
    whiskers.add_task(Task("Breakfast", at(8)))

    warnings = make_scheduler(buddy, whiskers).conflict_warnings()

    assert len(warnings) == 1
    assert "different pets" in warnings[0]


def test_no_conflict_warnings_when_times_differ():
    pet = Pet("Buddy", "Dog")
    pet.add_task(Task("Morning walk", at(7, 30)))
    pet.add_task(Task("Evening walk", at(18)))

    assert make_scheduler(pet).conflict_warnings() == []


def test_completed_task_is_not_a_conflict():
    pet = Pet("Buddy", "Dog")
    done = Task("Morning walk", at(7, 30))
    pet.add_task(done)
    pet.add_task(Task("Grooming", at(7, 30)))
    done.mark_complete()

    assert make_scheduler(pet).conflict_warnings() == []


def test_same_clock_time_on_different_days_is_not_a_conflict():
    pet = Pet("Buddy", "Dog")
    pet.add_task(Task("Walk", at(8, day=1)))
    pet.add_task(Task("Walk", at(8, day=2)))

    assert make_scheduler(pet).conflict_warnings() == []


def test_find_conflicts_returns_both_tasks_sharing_a_time():
    pet = Pet("Buddy", "Dog")
    a = Task("Walk", at(7, 30))
    b = Task("Grooming", at(7, 30))
    pet.add_task(a)
    pet.add_task(b)
    pet.add_task(Task("Dinner", at(18)))

    conflicts = make_scheduler(pet).find_conflicts()

    assert conflicts == [a, b]


def test_conflict_checks_on_pet_with_no_tasks_return_empty():
    scheduler = make_scheduler(Pet("Buddy", "Dog"))

    assert scheduler.conflict_warnings() == []
    assert scheduler.find_conflicts() == []
