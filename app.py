import streamlit as st

from pawpal import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
PawPal+ helps a pet owner convert care tasks into a daily plan. Add tasks, then generate a schedule
that balances priority, duration, and availability.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

This version includes task scheduling logic and a simple explanation layer.
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

st.subheader("Quick Demo Inputs")
owner_name = st.text_input("Owner name", value="Jordan")
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])

st.markdown("### Tasks")
st.caption("Add a few tasks. These tasks will be used to build a daily schedule.")

if "tasks" not in st.session_state:
    st.session_state.tasks = []

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

if st.button("Add task"):
    st.session_state.tasks.append(
        {"title": task_title, "duration_minutes": int(duration), "priority": priority}
    )

if st.session_state.tasks:
    st.write("Current tasks:")
    st.table(st.session_state.tasks)
else:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")
st.caption("Generate a daily schedule from the current tasks.")

if st.button("Generate schedule"):
    owner = Owner(name=owner_name or "Jordan")
    pet = Pet(name=pet_name or "Mochi", species=species)
    tasks = [Task.from_dict(task_data) for task_data in st.session_state.tasks]
    scheduler = Scheduler()
    schedule, notes = scheduler.build_daily_schedule(owner=owner, pet=pet, tasks=tasks)
    conflicts = scheduler.detect_conflicts(owner=owner, tasks=tasks)

    if schedule:
        st.write("### Daily Schedule")
        st.table([item.to_row() for item in schedule])
        with st.expander("Why these tasks were chosen", expanded=True):
            for note in notes:
                st.write(f"- {note}")
    else:
        st.warning("No schedule could be created with the current tasks and availability.")

    if conflicts:
        st.error("Potential scheduling conflicts detected:")
        for conflict in conflicts:
            st.write(f"- {conflict}")
