# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

#Today's Schedule for Muzamil
========================================
07:30 AM  |  Buddy (Dog): Morning walk
08:00 AM  |  Whiskers (Cat): Breakfast feeding
06:00 PM  |  Buddy (Dog): Evening walk
07:30 PM  |  Whiskers (Cat): Brush fur
========================================

```
# e.g.:
# Daily plan for Biscuit (Golden Retriever):
#   08:00 — Morning walk (30 min) [priority: high]
#   09:00 — Feeding (10 min) [priority: high]
#   ...
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

## 📐 Smarter Scheduling

> Fill in once you've implemented scheduling logic.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | | e.g., by priority, duration |
| Filtering | | e.g., skip tasks if time runs out |
| Conflict handling | | e.g., overlapping time slots |
| Recurring tasks | | e.g., daily vs. weekly |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->


## Implementation Summary

PawPal is a pet care app that tracks activities for multiple pets and builds a daily schedule. The logic is in `pawpal_system.py`, `main.py` runs a demo, and `diagrams/uml.mmd` holds the class diagram.

### How the classes work together

- **Owner** has one or more pets. `get_all_tasks()` gathers every pet's tasks into one list.
- **Pet** holds its own `Task` list and its `Medication` list.
- **Task** is a single activity, such as a walk or feeding, with a time, frequency (once, daily or weekly) and completion status. It can carry a **TaskProgress**, which tracks progress toward a goal, for example `20% complete, 1/5 miles`.
- **Scheduler** is the "brain". It reads tasks through `Owner.get_all_tasks()`, so it covers all pets. It can:
  - sort tasks by time
  - list the pending tasks
  - work out reminder times
  - complete a task and add the next occurrence if it repeats
  - flag tasks scheduled for the same time
- **MedicationSearch** looks up a **Medication** in a catalog by name or by the illness it treats.

### Running it

- `python main.py` prints "Today's Schedule" for an owner with two pets.
- `python -m pytest tests` runs the tests.
