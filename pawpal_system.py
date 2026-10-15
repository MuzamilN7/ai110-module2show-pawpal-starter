from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

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
        """Mark done; return the next occurrence if the task repeats, else None."""
        self.completed = True
        delta = FREQUENCY_DELTAS.get(self.frequency)
        if delta is None:
            return None
        return Task(self.description, self.time + delta, self.frequency)


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
        """Return all tasks ordered from earliest to latest."""
        return sorted(self.get_tasks(), key=lambda t: t.time)

    def pending_tasks(self) -> List[Task]:
        """Return incomplete tasks ordered by time."""
        return [t for t in self.sort_by_time() if not t.completed]

    def set_reminder(self, task: Task, lead_time: timedelta = timedelta(minutes=15)) -> datetime:
        """Return when to remind the owner about a task."""
        return task.time - lead_time

    def due_reminders(self, now: Optional[datetime] = None) -> List[Task]:
        """Pending tasks whose reminder time has arrived."""
        now = now or datetime.now()
        return [t for t in self.pending_tasks() if self.set_reminder(t) <= now]

    def complete_task(self, pet: Pet, task: Task) -> None:
        """Complete a task and schedule its next occurrence if it repeats."""
        next_task = task.mark_complete()
        if next_task:
            pet.add_task(next_task)

    def find_conflicts(self) -> List[Task]:
        """Return pending tasks that share the exact same time as another."""
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
