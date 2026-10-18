from datetime import date, datetime, time

import streamlit as st
from pawpal_system import Owner, Pet, Scheduler, Task
st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

# Keep one Owner alive across Streamlit reruns.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan")
owner = st.session_state.owner

st.subheader("Owner")
owner.name = st.text_input("Owner name", value=owner.name)

st.subheader("Add a Pet")
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])

if st.button("Add pet"):
    if any(p.name == pet_name for p in owner.pets):
        st.warning(f"{pet_name} is already added.")
    else:
        owner.add_pet(Pet(name=pet_name, species=species))
        st.success(f"Added {pet_name} the {species}.")

if owner.pets:
    st.write("Your pets:")
    st.table([{"name": p.name, "species": p.species, "tasks": len(p.tasks)} for p in owner.pets])
else:
    st.info("No pets yet. Add one above.")

st.markdown("### Schedule a Task")

if owner.pets:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        task_pet = st.selectbox("Pet", [p.name for p in owner.pets])
    with col2:
        task_title = st.text_input("Task", value="Morning walk")
    with col3:
        task_time = st.time_input("Time", value=time(7, 30))
    with col4:
        frequency = st.selectbox("Frequency", ["once", "daily", "weekly"])

    if st.button("Add task"):
        pet = next(p for p in owner.pets if p.name == task_pet)
        pet.add_task(Task(task_title, datetime.combine(date.today(), task_time), frequency))
        st.success(f"Added '{task_title}' for {pet.name}.")
else:
    st.info("Add a pet before scheduling tasks.")

st.divider()

st.subheader("Today's Schedule")

if st.button("Generate schedule"):
    scheduler = Scheduler(owner)
    pet_for_task = {id(t): p for p in owner.pets for t in p.tasks}
    pending = scheduler.pending_tasks()

    if pending:
        st.table(
            [
                {
                    "time": f"{t.time:%I:%M %p}",
                    "pet": pet_for_task[id(t)].name,
                    "task": t.description,
                    "frequency": t.frequency,
                }
                for t in pending
            ]
        )
    else:
        st.info("No pending tasks. Add some above.")

    conflicts = scheduler.find_conflicts()
    if conflicts:
        st.warning("Some tasks are scheduled at the same time: "
                   + ", ".join(t.description for t in conflicts))
