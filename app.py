import streamlit as st
from datetime import date
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ---------------------------------------------------------------------------
# Profile setup
# ---------------------------------------------------------------------------
st.subheader("Owner & Pet Profile")

col_o, col_p, col_s, col_w, col_sl = st.columns(5)
with col_o:
    owner_name = st.text_input("Owner name", key="owner_name")
with col_p:
    pet_name = st.text_input("Pet name", key="pet_name")
with col_s:
    species = st.selectbox("Species", ["dog", "cat", "other"], key="species")
with col_w:
    wake_time = st.text_input("Wake time (HH:MM)", value="07:00", key="wake_time")
with col_sl:
    sleep_time = st.text_input("Sleep time (HH:MM)", value="22:00", key="sleep_time")

if st.button("Save Profile"):
    if owner_name and pet_name:
        if "owner" not in st.session_state:
            pet = Pet(name=pet_name, species=species, age=0, breed="")
            st.session_state.owner = Owner(
                name=owner_name,
                wake_time=wake_time,
                sleep_time=sleep_time,
                pets=[pet],
            )
            st.success(f"Profile created for {owner_name} with pet {pet_name}.")
        else:
            st.info("Profile already exists. Clear session to reset.")
    else:
        st.warning("Please enter both an owner name and a pet name.")

if "owner" in st.session_state:
    owner: Owner = st.session_state.owner
    pet_names = [p.name for p in owner.pets]
    st.caption(
        f"Active profile: **{owner.name}** | "
        f"Pets: {', '.join(f'**{n}**' for n in pet_names)} | "
        f"Hours: {owner.wake_time} – {owner.sleep_time}"
    )

st.divider()

# ---------------------------------------------------------------------------
# Add tasks
# ---------------------------------------------------------------------------
st.subheader("Add Task")

if "owner" not in st.session_state:
    st.info("Save a profile above before adding tasks.")
else:
    owner: Owner = st.session_state.owner
    pet_names = [p.name for p in owner.pets]

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        task_pet = st.selectbox("Pet", pet_names, key="task_pet")
    with col2:
        task_description = st.text_input("Description", key="task_description")
    with col3:
        task_time = st.text_input("Start (HH:MM)", key="task_time")
    with col4:
        task_duration = st.text_input("Duration (H:MM)", key="task_duration")
    with col5:
        task_frequency = st.selectbox(
            "Frequency", ["daily", "weekly", "monthly", "yearly"], key="task_frequency"
        )
    with col6:
        task_priority = st.selectbox(
            "Priority",
            [1, 2, 3],
            index=1,
            format_func=lambda x: {1: "High", 2: "Medium", 3: "Low"}[x],
            key="task_priority",
        )

    if st.button("Add Task"):
        if not task_description:
            st.warning("Description is required.")
        else:
            new_task = Task(
                description=task_description,
                time=task_time,
                duration=task_duration,
                frequency=task_frequency,
                priority=task_priority,
            )
            for pet in owner.pets:
                if pet.name == task_pet:
                    pet.add_task(new_task)
                    st.success(f"Task '{task_description}' added to {task_pet}.")
                    break

st.divider()

# ---------------------------------------------------------------------------
# Task list with filtering by pet and status
# ---------------------------------------------------------------------------
st.subheader("Task List")

if "owner" not in st.session_state:
    st.info("Save a profile to see tasks.")
else:
    owner: Owner = st.session_state.owner
    pet_names = [p.name for p in owner.pets]

    f_col1, f_col2 = st.columns(2)
    with f_col1:
        filter_pet = st.selectbox(
            "Filter by pet", ["All pets"] + pet_names, key="filter_pet"
        )
    with f_col2:
        filter_status = st.selectbox(
            "Filter by status",
            ["All", "Pending", "Completed"],
            key="filter_status",
        )

    # Gather tasks according to filters
    if filter_pet == "All pets":
        if filter_status == "All":
            tasks = [t for p in owner.pets for t in p.tasks]
            task_pets = [p.name for p in owner.pets for _ in p.tasks]
        elif filter_status == "Pending":
            tasks = owner.get_tasks_by_status(completed=False)
            task_pets = [
                p.name for p in owner.pets for t in p.tasks if not t.is_completed
            ]
        else:
            tasks = owner.get_tasks_by_status(completed=True)
            task_pets = [
                p.name for p in owner.pets for t in p.tasks if t.is_completed
            ]
    else:
        completed_flag = None if filter_status == "All" else (filter_status == "Completed")
        if completed_flag is None:
            tasks = [t for p in owner.pets if p.name == filter_pet for t in p.tasks]
        else:
            tasks = owner.get_tasks_for_pet(filter_pet, completed=completed_flag)
        task_pets = [filter_pet] * len(tasks)

    if tasks:
        priority_label = {1: "High", 2: "Medium", 3: "Low"}
        rows = [
            {
                "pet": tp,
                "description": t.description,
                "time": t.time,
                "duration": t.duration,
                "frequency": t.frequency,
                "priority": priority_label.get(t.priority, str(t.priority)),
                "completed": t.is_completed,
            }
            for t, tp in zip(tasks, task_pets)
        ]
        st.dataframe(rows, use_container_width=True)
    else:
        st.info("No tasks match the current filters.")

st.divider()

# ---------------------------------------------------------------------------
# Build & display schedule
# ---------------------------------------------------------------------------
st.subheader("Build Schedule")

if "owner" not in st.session_state:
    st.info("Save a profile to build a schedule.")
else:
    owner: Owner = st.session_state.owner

    sched_col1, sched_col2 = st.columns(2)
    with sched_col1:
        sched_date = st.date_input(
            "Schedule date",
            value=date.today(),
            key="sched_date",
            help="Weekly tasks run on Mondays, monthly on the 1st.",
        )
    with sched_col2:
        filter_sched_pet = st.selectbox(
            "Show tasks for",
            ["All pets"] + [p.name for p in owner.pets],
            key="filter_sched_pet",
        )

    if st.button("Generate Schedule"):
        if not owner.get_all_tasks():
            st.warning("Add at least one task before generating a schedule.")
        else:
            scheduler = Scheduler(owner)
            scheduler.build_schedule(reference_date=sched_date)

            # Apply pet filter to the schedule view
            if filter_sched_pet != "All pets":
                items = scheduler.filter_schedule(pet_name=filter_sched_pet)
            else:
                items = scheduler.schedule

            if not items:
                st.info("No tasks are due on this date for the selected pet.")
            else:
                priority_label = {1: "High", 2: "Medium", 3: "Low"}
                rows = [
                    {
                        "time": item.time_slot,
                        "pet": item.pet.name if item.pet else "?",
                        "task": item.task.description,
                        "duration": item.task.duration or "—",
                        "frequency": item.task.frequency,
                        "priority": priority_label.get(item.task.priority, str(item.task.priority)),
                    }
                    for item in items
                ]
                st.dataframe(rows, use_container_width=True)

                # Conflict detection — always run on full schedule, not filtered view
                conflicts = scheduler.detect_conflicts()
                if conflicts:
                    st.error(f"⚠️ {len(conflicts)} scheduling conflict(s) detected:")
                    for a, b in conflicts:
                        st.markdown(
                            f"- **{a.task.description}** ({a.time_slot}, "
                            f"{a.task.duration or '30m'}) overlaps with "
                            f"**{b.task.description}** ({b.time_slot})"
                        )
                else:
                    st.success("No scheduling conflicts.")

            # Raw text output (sorted, with conflicts)
            with st.expander("Raw schedule text"):
                st.text(scheduler.explain_schedule())
