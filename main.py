from datetime import datetime

from pawpal_system import Owner, Pet, Scheduler, Task


def today_at(hour: int, minute: int = 0) -> datetime:
    """Build a datetime for today at the given time."""
    return datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)


def build_owner() -> Owner:
    """Create an owner with two pets and a few tasks each."""
    owner = Owner(name="Muzamil")

    buddy = Pet(name="Buddy", species="Dog")
    whiskers = Pet(name="Whiskers", species="Cat")
    owner.add_pet(buddy)
    owner.add_pet(whiskers)

    # Tasks are added out of order on purpose, so the scheduler has to sort them.
    buddy.add_task(Task("Evening walk", today_at(18, 0), frequency="daily"))
    buddy.add_task(Task("Morning walk", today_at(7, 30), frequency="daily"))
    whiskers.add_task(Task("Breakfast feeding", today_at(8, 0), frequency="daily"))
    whiskers.add_task(Task("Brush fur", today_at(19, 30), frequency="weekly"))

    # Deliberate conflicts to demo detection: one across pets, one on the same pet.
    buddy.add_task(Task("Give medication", today_at(8, 0)))  # clashes with Whiskers' breakfast
    buddy.add_task(Task("Grooming", today_at(7, 30)))  # clashes with Buddy's morning walk

    return owner


def print_schedule(owner: Owner) -> None:
    """Print every pending task across all pets, ordered by time."""
    scheduler = Scheduler(owner)

    # Tasks don't know which pet they belong to, so build a lookup for display.
    pet_for_task = {id(task): pet for pet in owner.pets for task in pet.tasks}

    print(f"Today's Schedule for {owner.name}")
    print("=" * 40)

    for task in scheduler.pending_tasks():
        pet = pet_for_task[id(task)]
        print(f"{task.time:%I:%M %p}  |  {pet.name} ({pet.species}): {task.description}")

    print("=" * 40)

    for warning in scheduler.conflict_warnings():
        print(warning)


if __name__ == "__main__":
    print_schedule(build_owner())
