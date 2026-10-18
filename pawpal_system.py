from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

FREQUENCY_DELTAS = {
    "once": None,
    "daily": timedelta(days=1),
    "weekly": timedelta(weeks=1),
}


@dataclass
class Medication:
    name: str
    description: str
    treats: List[str] = field(default_factory=list)


@dataclass
class TaskProgress:
    task_type: str
    amount_needed: float
    amount_completed: float = 0.0
    unit: str = ""

    def calculate_percent(self) -> float:
        """Return amount_completed as a percentage of amount_needed (capped at 100)."""
        if self.amount_needed <= 0:
            return 0.0
        return min(self.amount_completed / self.amount_needed * 100, 100.0)

    def get_status(self) -> str:
        """Return a summary such as '20% complete, 1/5 miles'."""
        percent = self.calculate_percent()
        unit = f" {self.unit}" if self.unit else ""
        return (
            f"{percent:.0f}% complete, "
            f"{self.amount_completed:g}/{self.amount_needed:g}{unit}"
        )


@dataclass
class Task:
    """A single activity such as walking, feeding, or general care."""
    description: str
    time: datetime
    frequency: str = "once"  # "once", "daily", or "weekly"
    completed: bool = False
    progress: Optional[TaskProgress] = None

    def mark_complete(self) -> Optional["Task"]:
        """Mark the task done and return the next occurrence if it repeats.

        Returns:
            A new Task for a "daily" or "weekly" task, or None for a "once" task or
            one that was already completed (so repeat calls never create duplicates).

        The next time is the scheduled time plus one period (a timedelta), not the
        completion time, so the routine does not drift. If that time is already in
        the past (a badly overdue task), whole periods are added until it is in the
        future.
        """
        if self.completed:  # already done: don't spawn a duplicate occurrence
            return None
        self.completed = True
        delta = FREQUENCY_DELTAS.get(self.frequency)
        if delta is None:
            return None
        # Anchor to the scheduled time (not completion time) so the routine doesn't drift,
        # but skip any occurrences already in the past if the task was badly overdue.
        next_time = self.time + delta
        now = datetime.now()
        while next_time <= now:
            next_time += delta
        return Task(self.description, next_time, self.frequency)


@dataclass
class Pet:
    name: str
    species: str
    tasks: List[Task] = field(default_factory=list)
    medications: List[Medication] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove a task from this pet's task list."""
        self.tasks.remove(task)


@dataclass
class Owner:
    name: str
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's list of pets."""
        self.pets.append(pet)

    def get_all_tasks(self) -> List[Task]:
        """Return every pet's tasks together."""
        return [task for pet in self.pets for task in pet.tasks]


class Scheduler:
    """The 'brain': retrieves and organizes tasks across all of an owner's pets."""

    def __init__(self, owner: Owner):
        """Create a scheduler that manages the given owner's pets."""
        self.owner = owner

    def get_tasks(self) -> List[Task]:
        """Read tasks from the Owner so every pet is included."""
        return self.owner.get_all_tasks()

    def sort_by_time(self) -> List[Task]:
        """Return every task across all pets, ordered from earliest to latest.

        Uses sorted() with a lambda key on Task.time (a datetime), so ordering is
        correct across dates as well as times of day. The original lists are not
        modified. Runs in O(n log n).
        """
        return sorted(self.get_tasks(), key=lambda t: t.time)

    def pending_tasks(self) -> List[Task]:
        """Return incomplete tasks across all pets, ordered by time.

        Built on sort_by_time(), then drops any task whose completed flag is set.
        """
        return [t for t in self.sort_by_time() if not t.completed]

    def filter_tasks(self, completed: Optional[bool] = None, pet_name: Optional[str] = None) -> List[Task]:
        """Return tasks (ordered by time) matching completion status and/or pet name.

        Args:
            completed: True for finished tasks, False for pending ones, None for both.
            pet_name: Only include this pet's tasks (case-insensitive); None for all pets.

        Returns:
            Matching tasks sorted by time. Both filters apply together, and an
            unknown pet name gives an empty list rather than an error.

        Tasks do not store their pet, so this walks owner.pets and filters from there.
        """
        matches = [
            (pet, task)
            for pet in self.owner.pets
            if pet_name is None or pet.name.lower() == pet_name.lower()
            for task in pet.tasks
            if completed is None or task.completed == completed
        ]
        return [task for _, task in sorted(matches, key=lambda pt: pt[1].time)]

    def set_reminder(self, task: Task, lead_time: timedelta = timedelta(minutes=15)) -> datetime:
        """Return when to remind the owner about a task."""
        return task.time - lead_time

    def due_reminders(self, now: Optional[datetime] = None) -> List[Task]:
        """Return pending tasks whose reminder time has arrived.

        Args:
            now: The moment to check against; defaults to datetime.now().

        A task is due when set_reminder(task) (its time minus the lead time) is at or
        before now. Results are ordered by task time.
        """
        now = now or datetime.now()
        return [t for t in self.pending_tasks() if self.set_reminder(t) <= now]

    def complete_task(self, pet: Pet, task: Task) -> None:
        """Complete a task and add its next occurrence to the pet if it repeats.

        Args:
            pet: The pet that owns the task; the new occurrence is added to it.
            task: The task to complete.

        Delegates the date math to Task.mark_complete(). Nothing is added for "once"
        tasks or tasks that were already completed.
        """
        next_task = task.mark_complete()
        if next_task:
            pet.add_task(next_task)

    def conflict_warnings(self) -> List[str]:
        """Return a warning message for each time slot with 2+ pending tasks.

        Returns:
            One string per conflicting time slot, ordered by time, naming the pet and
            task for each entry and whether the clash is on the "same pet" or
            "different pets". An empty list means no conflicts.

        Lightweight check: pending tasks are bucketed by exact start time in one
        O(n) pass (plus sorting the slots), so it never raises and never blocks
        scheduling; it only reports. Only identical start times count as conflicts;
        overlapping durations are not detected.
        """
        slots: Dict[datetime, List[Tuple[Pet, Task]]] = {}
        for pet in self.owner.pets:
            for task in pet.tasks:
                if not task.completed:
                    slots.setdefault(task.time, []).append((pet, task))

        warnings: List[str] = []
        for time in sorted(slots):
            entries = slots[time]
            if len(entries) < 2:
                continue
            names = {pet.name for pet, _ in entries}
            scope = "same pet" if len(names) == 1 else "different pets"
            details = ", ".join(f"{pet.name}: {task.description}" for pet, task in entries)
            warnings.append(f"WARNING: {len(entries)} tasks at {time:%I:%M %p} ({scope}) -> {details}")
        return warnings

    def find_conflicts(self) -> List[Task]:
        """Return pending tasks that share the exact same time as another.

        Unlike conflict_warnings(), this returns Task objects without pet info. Note
        that when three or more tasks share a time, the first one is listed more than
        once.
        """
        seen: Dict[datetime, Task] = {}
        conflicts: List[Task] = []
        for task in self.pending_tasks():
            if task.time in seen:
                conflicts.extend([seen[task.time], task])
            else:
                seen[task.time] = task
        return conflicts


class MedicationSearch:
    def __init__(self, catalog: Optional[List[Medication]] = None):
        """Create a searchable catalog, empty by default."""
        self.catalog = catalog or []

    def search_medication(self, medication_name: str = "", illness_type: str = "") -> Optional[Medication]:
        """Look up a medication by name or by the illness it treats."""
        name = medication_name.lower()
        illness = illness_type.lower()
        for med in self.catalog:
            if name and med.name.lower() == name:
                return med
            if illness and illness in (t.lower() for t in med.treats):
                return med
        return None

    def get_description(self, medication: Optional[Medication]) -> str:
        """Return the description of a medication."""
        return medication.description if medication else "No medication found."
