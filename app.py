import streamlit as st
from datetime import date
from pawpal_system import Owner, Pet, Task, Scheduler, ScheduledItem

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------
if "owners" not in st.session_state:
    st.session_state.owners = {}          # {owner_name: Owner}
if "active_owner_name" not in st.session_state:
    st.session_state.active_owner_name = None
if "prev_active_owner_name" not in st.session_state:
    st.session_state.prev_active_owner_name = None

_FORM_KEYS = [
    "owner_name", "wake_time", "sleep_time", "owner_notes",
    "pet_name", "species", "species_other", "pet_age", "pet_breed",
    "pet_diet", "pet_meds", "pet_notes",
    "new_pet_name", "new_pet_species", "new_pet_species_other",
    "new_pet_age", "new_pet_breed", "new_pet_diet", "new_pet_meds", "new_pet_notes",
    "task_description", "task_time", "task_duration",
    "task_due_date_enabled", "task_due_date",
]

def _clear_form_keys():
    for k in _FORM_KEYS:
        st.session_state.pop(k, None)

# Clear fields when the active owner changes
if st.session_state.active_owner_name != st.session_state.prev_active_owner_name:
    _clear_form_keys()
    st.session_state.prev_active_owner_name = st.session_state.active_owner_name

# ---------------------------------------------------------------------------
# Owner switcher
# ---------------------------------------------------------------------------
if st.session_state.owners:
    owner_names = list(st.session_state.owners.keys())
    sw_col, del_col = st.columns([4, 1])
    with sw_col:
        selected = st.selectbox(
            "Active owner",
            owner_names,
            index=owner_names.index(st.session_state.active_owner_name)
                  if st.session_state.active_owner_name in owner_names else 0,
            key="owner_switcher",
        )
    with del_col:
        st.markdown("&nbsp;", unsafe_allow_html=True)
        if st.button("🗑️ Delete owner", key="delete_owner"):
            del st.session_state.owners[st.session_state.active_owner_name]
            remaining = list(st.session_state.owners.keys())
            st.session_state.active_owner_name = remaining[0] if remaining else None
            _clear_form_keys()
            st.rerun()
    if selected != st.session_state.active_owner_name:
        st.session_state.active_owner_name = selected
        st.rerun()
    st.divider()

# Helper to get the active owner (may be None)
def active_owner() -> Owner | None:
    return st.session_state.owners.get(st.session_state.active_owner_name)

# ---------------------------------------------------------------------------
# Profile setup
# ---------------------------------------------------------------------------
st.subheader("Owner & Pet Profile")

st.markdown("**Owner Info**")
col_o, col_w, col_sl = st.columns(3)
with col_o:
    owner_name = st.text_input("Owner name", key="owner_name")
with col_w:
    wake_time = st.text_input("Wake time (HH:MM)", value="07:00", key="wake_time")
with col_sl:
    sleep_time = st.text_input("Sleep time (HH:MM)", value="22:00", key="sleep_time")

owner_notes = st.text_input("Additional notes (comma-separated)", key="owner_notes")

st.markdown("**First Pet Info**")
col_p, col_s, col_a, col_b = st.columns(4)
with col_p:
    pet_name = st.text_input("Pet name", key="pet_name")
with col_s:
    species = st.selectbox("Species", ["dog", "cat", "other"], key="species")
    if species == "other":
        species = st.text_input("Please specify species", key="species_other")
with col_a:
    pet_age = st.number_input("Age (years)", min_value=0, max_value=50, step=1, key="pet_age")
with col_b:
    pet_breed = st.text_input("Breed", key="pet_breed")

pet_diet = st.text_input("Dietary restrictions (comma-separated)", key="pet_diet",
                          help="e.g. grain-free, no dairy")
pet_meds = st.text_input("Medications (comma-separated)", key="pet_meds")
pet_notes = st.text_input("Additional notes (comma-separated)", key="pet_notes")

if st.button("Save Profile"):
    if owner_name and pet_name:
        new_pet = Pet(
            name=pet_name,
            species=species,
            age=int(pet_age),
            breed=pet_breed,
            dietary_restrictions=[x.strip() for x in pet_diet.split(",") if x.strip()],
            medication_information=[x.strip() for x in pet_meds.split(",") if x.strip()],
            additional_information=[x.strip() for x in pet_notes.split(",") if x.strip()],
        )
        if owner_name not in st.session_state.owners:
            # Create new owner
            st.session_state.owners[owner_name] = Owner(
                name=owner_name,
                wake_time=wake_time,
                sleep_time=sleep_time,
                pets=[new_pet],
                additional_information=[x.strip() for x in owner_notes.split(",") if x.strip()],
            )
            st.session_state.active_owner_name = owner_name
            st.success(f"Profile created for {owner_name} with pet {pet_name}.")
        else:
            # Update existing owner
            owner = st.session_state.owners[owner_name]
            owner.wake_time = wake_time
            owner.sleep_time = sleep_time
            owner.additional_information = [x.strip() for x in owner_notes.split(",") if x.strip()]
            existing_pet = next((p for p in owner.pets if p.name.lower() == pet_name.lower()), None)
            if existing_pet:
                existing_pet.species = species
                existing_pet.age = int(pet_age)
                existing_pet.breed = pet_breed
                existing_pet.dietary_restrictions = [x.strip() for x in pet_diet.split(",") if x.strip()]
                existing_pet.medication_information = [x.strip() for x in pet_meds.split(",") if x.strip()]
                existing_pet.additional_information = [x.strip() for x in pet_notes.split(",") if x.strip()]
                st.success(f"Profile updated for {owner_name} and pet {pet_name}.")
            else:
                owner.add_pet(new_pet)
                st.success(f"Owner info updated and new pet {pet_name} added.")
        st.rerun()
    else:
        st.warning("Please enter both an owner name and a pet name.")

owner = active_owner()
if owner:
    pet_names = [p.name for p in owner.pets]
    st.caption(
        f"Active profile: **{owner.name}** | "
        f"Pets: {', '.join(f'**{n}**' for n in pet_names)} | "
        f"Hours: {owner.wake_time} – {owner.sleep_time}"
    )
    oi1, oi2, oi3 = st.columns(3)
    oi1.metric("Owner", owner.name)
    oi2.metric("Wake time", owner.wake_time)
    oi3.metric("Sleep time", owner.sleep_time)
    if owner.additional_information:
        st.markdown(f"**Notes:** {', '.join(owner.additional_information)}")

st.divider()

# ---------------------------------------------------------------------------
# Add pet
# ---------------------------------------------------------------------------
st.subheader("Add Pet")

owner = active_owner()
if not owner:
    st.info("Save a profile above before adding pets.")
else:
    ap_col1, ap_col2, ap_col3, ap_col4 = st.columns(4)
    with ap_col1:
        new_pet_name = st.text_input("Pet name", key="new_pet_name")
    with ap_col2:
        new_pet_species = st.selectbox("Species", ["dog", "cat", "other"], key="new_pet_species")
        if new_pet_species == "other":
            new_pet_species = st.text_input("Please specify species", key="new_pet_species_other")
    with ap_col3:
        new_pet_age = st.number_input("Age (years)", min_value=0, max_value=50, step=1, key="new_pet_age")
    with ap_col4:
        new_pet_breed = st.text_input("Breed", key="new_pet_breed")

    new_pet_diet = st.text_input("Dietary restrictions (comma-separated)", key="new_pet_diet")
    new_pet_meds = st.text_input("Medications (comma-separated)", key="new_pet_meds")
    new_pet_notes = st.text_input("Additional notes (comma-separated)", key="new_pet_notes")

    if st.button("Add / Update Pet"):
        if not new_pet_name:
            st.warning("Please enter a pet name.")
        else:
            existing_pet = next((p for p in owner.pets if p.name.lower() == new_pet_name.lower()), None)
            if existing_pet:
                existing_pet.species = new_pet_species
                existing_pet.age = int(new_pet_age)
                existing_pet.breed = new_pet_breed
                existing_pet.dietary_restrictions = [x.strip() for x in new_pet_diet.split(",") if x.strip()]
                existing_pet.medication_information = [x.strip() for x in new_pet_meds.split(",") if x.strip()]
                existing_pet.additional_information = [x.strip() for x in new_pet_notes.split(",") if x.strip()]
                st.success(f"Pet '{new_pet_name}' updated!")
            else:
                owner.add_pet(Pet(
                    name=new_pet_name,
                    species=new_pet_species,
                    age=int(new_pet_age),
                    breed=new_pet_breed,
                    dietary_restrictions=[x.strip() for x in new_pet_diet.split(",") if x.strip()],
                    medication_information=[x.strip() for x in new_pet_meds.split(",") if x.strip()],
                    additional_information=[x.strip() for x in new_pet_notes.split(",") if x.strip()],
                ))
                st.success(f"Pet '{new_pet_name}' added!")

# ---------------------------------------------------------------------------
# Pet profiles viewer
# ---------------------------------------------------------------------------
st.divider()
st.subheader("Pet Profiles")

owner = active_owner()
if not owner:
    st.info("Save a profile to view pet profiles.")
else:
    if not owner.pets:
        st.info("No pets added yet.")
    else:
        for pet in list(owner.pets):
            with st.expander(f"{pet.name} — {pet.species.capitalize()}"):
                c1, c2 = st.columns(2)
                c1.metric("Age", f"{pet.age} yr{'s' if pet.age != 1 else ''}")
                c2.metric("Tasks", len(pet.tasks))
                st.text(pet.get_info())

                if st.button(f"🗑️ Delete {pet.name}", key=f"delete_pet_{pet.name}"):
                    owner.pets = [p for p in owner.pets if p is not pet]
                    st.rerun()

# ---------------------------------------------------------------------------
# Add tasks
# ---------------------------------------------------------------------------
st.divider()
st.subheader("Add Task")

owner = active_owner()
if not owner:
    st.info("Save a profile above before adding tasks.")
else:
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

    use_due_date = st.checkbox("Set a due date", key="task_due_date_enabled")
    task_due_date = None
    if use_due_date:
        task_due_date = st.date_input("Due date", value=date.today(), key="task_due_date")

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
                due_date=task_due_date,
            )
            for pet in owner.pets:
                if pet.name == task_pet:
                    if any(t.description.lower() == task_description.lower() for t in pet.tasks):
                        st.warning(f"'{task_description}' already exists for {task_pet}.")
                    else:
                        pet.add_task(new_task)
                        st.success(f"Task '{task_description}' added to {task_pet}.")
                    break

st.divider()

# ---------------------------------------------------------------------------
# Task list with filtering by pet and status
# ---------------------------------------------------------------------------
st.subheader("Task List")

owner = active_owner()
if not owner:
    st.info("Save a profile to see tasks.")
else:
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

    scheduler = Scheduler(owner)
    pet_filter = None if filter_pet == "All pets" else filter_pet
    completed_flag = None if filter_status == "All" else (filter_status == "Completed")

    tasks = scheduler.filter_tasks(pet_name=pet_filter, completed=completed_flag)
    tasks = scheduler.sort_by_time(tasks)

    task_to_pet = {id(t): p.name for p in owner.pets for t in p.tasks}

    all_tasks = scheduler.filter_tasks(pet_name=pet_filter)
    n_pending = sum(1 for t in all_tasks if not t.is_completed)
    n_completed = sum(1 for t in all_tasks if t.is_completed)

    m1, m2, m3 = st.columns(3)
    m1.metric("Total tasks", len(all_tasks))
    m2.metric("Pending", n_pending)
    m3.metric("Completed", n_completed)

    if tasks:
        priority_badge = {1: "🔴 High", 2: "🟡 Medium", 3: "🟢 Low"}
        header = st.columns([1, 3, 1, 1, 1, 1, 1, 1])
        for col, label in zip(header, ["Done", "Description", "Pet", "Time", "Duration", "Frequency", "Priority", "Delete"]):
            col.markdown(f"**{label}**")

        # Build a lookup from task id to pet object for deletion
        task_to_pet_obj = {id(t): p for p in owner.pets for t in p.tasks}

        for i, t in enumerate(tasks):
            cols = st.columns([1, 3, 1, 1, 1, 1, 1, 1])
            checked = cols[0].checkbox("", value=t.is_completed, key=f"complete_{id(t)}_{i}")
            if checked and not t.is_completed:
                pet = task_to_pet_obj.get(id(t))
                Scheduler(owner).complete_task(ScheduledItem(task=t, time_slot=t.time or owner.wake_time, pet=pet))
                st.rerun()
            elif not checked and t.is_completed:
                t.is_completed = False
                st.rerun()
            cols[1].write(t.description)
            cols[2].write(task_to_pet.get(id(t), "?"))
            cols[3].write(t.time or "—")
            cols[4].write(t.duration or "—")
            cols[5].write(t.frequency.capitalize())
            cols[6].write(priority_badge.get(t.priority, str(t.priority)))
            if cols[7].button("🗑️", key=f"delete_{id(t)}_{i}"):
                pet = task_to_pet_obj.get(id(t))
                if pet:
                    pet.remove_task(t.description)
                st.rerun()

        if filter_status == "Pending" and n_pending == 0:
            st.success("All tasks are completed!")
    else:
        st.info("No tasks match the current filters.")

st.divider()

# ---------------------------------------------------------------------------
# Build & display schedule
# ---------------------------------------------------------------------------
st.subheader("Build Schedule")

owner = active_owner()
if not owner:
    st.info("Save a profile to build a schedule.")
else:
    sched_col1, sched_col2 = st.columns(2)
    with sched_col1:
        sched_date = st.date_input(
            "Schedule date",
            value=date.today(),
            key="sched_date",
        )
    with sched_col2:
        filter_sched_pet = st.selectbox(
            "Show tasks for",
            ["All pets"] + [p.name for p in owner.pets],
            key="filter_sched_pet",
        )

    if st.button("Generate Schedule"):
        if not any(p.tasks for p in owner.pets):
            st.warning("Add at least one task before generating a schedule.")
        else:
            scheduler = Scheduler(owner)
            scheduler.build_schedule(reference_date=sched_date)

            if filter_sched_pet != "All pets":
                items = scheduler.filter_schedule(pet_name=filter_sched_pet)
            else:
                items = scheduler.schedule

            if not items:
                st.info("No tasks are due on this date for the selected pet.")
            else:
                st.caption(f"{len(items)} task(s) scheduled — sorted by time, then priority.")
                priority_badge = {1: "🔴 High", 2: "🟡 Medium", 3: "🟢 Low"}
                rows = [
                    {
                        "Time": item.time_slot,
                        "Pet": item.pet.name if item.pet else "?",
                        "Task": item.task.description,
                        "Duration": item.task.duration or "—",
                        "Frequency": item.task.frequency.capitalize(),
                        "Priority": priority_badge.get(item.task.priority, str(item.task.priority)),
                    }
                    for item in items
                ]
                st.table(rows)

                conflicts = scheduler.detect_conflicts()
                if conflicts:
                    lines = "\n".join(
                        f"- **{a.task.description}** at {a.time_slot} "
                        f"({a.task.duration or '30m'}) overlaps **{b.task.description}** "
                        f"at {b.time_slot}"
                        for a, b in conflicts
                    )
                    st.warning(f"⚠️ {len(conflicts)} scheduling conflict(s) detected:\n{lines}")
                else:
                    st.success("No scheduling conflicts — your day looks clean!")

