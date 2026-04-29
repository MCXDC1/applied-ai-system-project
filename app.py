import logging
import os
import re
from datetime import date, timedelta

from dotenv import load_dotenv
load_dotenv()

import streamlit as st

from hotel_system import Hotel, HotelGuest
from pawpal_system import Pet, Task
from rag_engine import RAGEngine
from schedule_generator import (
    HotelScheduleGenerator, TOXIC_MEDICATIONS, find_toxic_instructions, _INJECTION_PATTERNS
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(page_title="PawPal Hotel", page_icon="🏨", layout="wide")
st.title("🏨 PawPal Hotel Scheduler")
st.caption("AI-powered daily scheduling for pet hotels — powered by RAG + Groq")

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "hotel" not in st.session_state:
    st.session_state.hotel = Hotel.load()
if "ai_result" not in st.session_state:
    st.session_state.ai_result = None


# ---------------------------------------------------------------------------
# Cached resources (survive Streamlit reruns)
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner="Loading pet care knowledge base...")
def get_rag_engine() -> RAGEngine | Exception:
    """Returns a ready RAGEngine, or the exception if startup failed."""
    try:
        engine = RAGEngine()
        n = engine.index_documents()
        logger.info("RAG engine ready with %d chunks", n)
        return engine
    except Exception as exc:
        logger.error("RAG engine failed to initialize: %s", exc)
        return exc


@st.cache_resource(show_spinner=False)
def get_generator() -> HotelScheduleGenerator | None:
    if not os.environ.get("GROQ_API_KEY"):
        return None
    rag = get_rag_engine()
    if isinstance(rag, Exception):
        return None
    try:
        return HotelScheduleGenerator(rag)
    except EnvironmentError:
        return None


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
hotel: Hotel = st.session_state.hotel

_SPECIES_OPTIONS = ["Dog", "Cat", "Rabbit", "Guinea Pig", "Bird", "Hamster", "Other"]
_ADMIN_METHODS = ["In food", "Oral / syringe", "Eye drops", "Ear drops", "Topical", "Injection", "Other"]
_FREQ_OPTIONS = ["Once daily", "Twice daily", "Three times daily", "Every other day", "Weekly", "As needed"]


def _parse_csv(value: str) -> list[str]:
    return [x.strip() for x in value.split(",") if x.strip()]


def _pet_flags(pet: Pet, special_instructions: str = "") -> tuple[list[str], list[str], list[str]]:
    """Return (toxic_meds, safe_meds, dangerous_instructions) for a pet."""
    toxic_terms = TOXIC_MEDICATIONS.get(pet.species.lower(), [])
    toxic = [m for m in pet.medication_information if any(t in m.lower() for t in toxic_terms)]
    safe = [m for m in pet.medication_information if m not in toxic]
    combined_text = " ".join(pet.additional_information) + " " + special_instructions
    dangerous = find_toxic_instructions(pet.species, combined_text)
    return toxic, safe, dangerous


def _expander_label(guest: HotelGuest) -> str:
    """Build the expander title with inline flag badges."""
    pet = guest.pet
    toxic, safe, dangerous = _pet_flags(pet, guest.special_instructions)
    badges = []
    if toxic or dangerous:
        badges.append("🚨 DANGER")
    if safe:
        badges.append("💊 Medication")
    if pet.dietary_restrictions:
        badges.append("🥗 Diet")
    badge_str = "  " + "  ".join(badges) if badges else ""
    return (
        f"{pet.name} — {pet.species.capitalize()} ({pet.breed}) | "
        f"Owner: {guest.owner_name}{badge_str}"
    )


# ---------------------------------------------------------------------------
# Sidebar — hotel settings & quick stats
# ---------------------------------------------------------------------------
_TIME_RE = re.compile(r"^\d{2}:\d{2}$")

with st.sidebar:
    st.header("Hotel Settings")
    hotel.name = st.text_input("Hotel name", value=hotel.name)
    _open_input = st.text_input("Opens (HH:MM)", value=hotel.open_time)
    _close_input = st.text_input("Closes (HH:MM)", value=hotel.close_time)
    if not _TIME_RE.match(_open_input):
        st.error("Open time must be in HH:MM format (e.g. 07:00).")
    else:
        hotel.open_time = _open_input
    if not _TIME_RE.match(_close_input):
        st.error("Close time must be in HH:MM format (e.g. 20:00).")
    else:
        hotel.close_time = _close_input

    st.divider()
    st.subheader("Today's Stats")
    today_guests = hotel.get_current_guests()
    st.metric("Current guests", len(today_guests))
    breakdown = hotel.species_breakdown()
    for species, count in breakdown.items():
        st.metric(species.capitalize() + "s", count)

    st.divider()
    if not os.environ.get("GROQ_API_KEY"):
        st.warning("GROQ_API_KEY not set. AI schedule will be unavailable.")
    else:
        st.success("API key detected")

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_checkin, tab_guests, tab_ai_schedule, tab_manual = st.tabs([
    "Check In", "Current Guests", "AI Schedule", "Manual Tasks"
])

# ===========================================================================
# TAB 1 — CHECK IN
# ===========================================================================
if "pending_meds" not in st.session_state:
    st.session_state.pending_meds = []
if "med_input_key" not in st.session_state:
    st.session_state.med_input_key = 0

with tab_checkin:
    st.subheader("Check In a New Guest")

    st.markdown("**Owner Information**")
    oc1, oc2 = st.columns(2)
    with oc1:
        owner_name = st.text_input("Owner name *", key="ci_owner_name")
    with oc2:
        owner_phone = st.text_input("Owner phone *", key="ci_owner_phone")

    st.markdown("**Pet Information**")
    pc1, pc2, pc3, pc4 = st.columns(4)
    with pc1:
        pet_name = st.text_input("Pet name *", key="ci_pet_name")
    with pc2:
        pet_species_sel = st.selectbox("Species", _SPECIES_OPTIONS, key="ci_species")
        if pet_species_sel == "Other":
            pet_species = st.text_input("Specify species", key="ci_species_other")
        else:
            pet_species = pet_species_sel
    with pc3:
        pet_age = st.number_input("Age (years)", min_value=0, max_value=50, step=1, key="ci_age")
    with pc4:
        pet_breed = st.text_input("Breed", key="ci_breed")

    pet_diet = st.text_input("Dietary restrictions (comma-separated)",
                             help="e.g. grain-free, no chicken", key="ci_diet")

    st.markdown("**Medications**")

    # Show already-added medications
    for _mi, _med in enumerate(st.session_state.pending_meds):
        _rc1, _rc2 = st.columns([8, 1])
        _rc1.write(f"• {_med}")
        if _rc2.button("✕", key=f"remove_med_{_mi}"):
            st.session_state.pending_meds.pop(_mi)
            st.rerun()

    # Medication builder — always visible, dropdowns appear immediately
    _mk = st.session_state.med_input_key
    _bc1, _bc2, _bc3 = st.columns(3)
    with _bc1:
        _new_name = st.text_input("Medication name", key=f"new_med_name_{_mk}")
    with _bc2:
        _new_freq = st.selectbox("Frequency", _FREQ_OPTIONS, key=f"new_med_freq_{_mk}")
    with _bc3:
        _new_method = st.selectbox("Administration", _ADMIN_METHODS, key=f"new_med_method_{_mk}")

    if _new_method == "Other":
        _new_custom = st.text_input("How should it be administered?", key=f"new_med_custom_{_mk}")
    else:
        _new_custom = ""

    if st.button("Add Medication", disabled=not _new_name.strip()):
        _method_final = _new_custom.strip() if _new_method == "Other" and _new_custom.strip() else _new_method
        st.session_state.pending_meds.append(f"{_new_name.strip()} — {_new_freq} — {_method_final}")
        st.session_state.med_input_key += 1  # resets the input fields
        st.rerun()

    pet_notes = st.text_input("Additional notes (comma-separated)",
                              help="e.g. fearful of loud noises, needs slow introduction",
                              key="ci_notes")
    special_instructions = st.text_area("Special instructions from owner", height=80,
                                        key="ci_special")

    st.markdown("**Stay Dates**")
    dc1, dc2 = st.columns(2)
    with dc1:
        check_in_date = st.date_input("Check-in date", value=date.today(), key="ci_checkin")
    with dc2:
        check_out_date = st.date_input("Check-out date",
                                       value=date.today() + timedelta(days=1), key="ci_checkout")

    if st.button("Check In Pet", type="primary"):
        errors = []
        if not owner_name.strip():
            errors.append("Owner name is required.")
        if not owner_phone.strip():
            errors.append("Owner phone is required.")
        if not pet_name.strip():
            errors.append("Pet name is required.")
        if not pet_species.strip():
            errors.append("Species is required — please specify the species.")
        if check_out_date < check_in_date:
            errors.append("Check-out date must be on or after check-in date.")

        if check_in_date < date.today() and not errors:
            st.warning(
                f"Check-in date {check_in_date} is in the past. "
                "This guest won't appear in today's current guests view."
            )

        if errors:
            for e in errors:
                st.error(e)
        else:
            pet = Pet(
                name=pet_name.strip(),
                species=pet_species.lower(),
                age=int(pet_age),
                breed=pet_breed.strip(),
                dietary_restrictions=_parse_csv(pet_diet),
                medication_information=list(st.session_state.pending_meds),
                additional_information=_parse_csv(pet_notes),
            )
            guest = HotelGuest(
                pet=pet,
                owner_name=owner_name.strip(),
                owner_phone=owner_phone.strip(),
                check_in=check_in_date,
                check_out=check_out_date,
                special_instructions=special_instructions.strip(),
            )
            try:
                hotel.check_in(guest)
                logger.info("Checked in %s for owner %s", pet_name, owner_name)
                st.success(f"{pet_name} has been checked in! ({check_in_date} → {check_out_date})")
                st.session_state.pending_meds = []
                st.session_state.med_input_key += 1
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

# ===========================================================================
# TAB 2 — CURRENT GUESTS
# ===========================================================================
with tab_guests:
    st.subheader("Current Guests")

    if "editing_pet" not in st.session_state:
        st.session_state.editing_pet = None

    view_date = st.date_input("View guests for date", value=date.today(), key="view_date")
    guests = hotel.get_current_guests(view_date)

    if not guests:
        st.info("No pets checked in for this date.")
    else:
        for guest in guests:
            pet = guest.pet
            # Unique key per guest: name + phone covers same-name pets from different owners
            gkey = f"{pet.name}_{guest.owner_phone.replace(' ', '_')}"
            is_editing = st.session_state.editing_pet == gkey

            with st.expander(_expander_label(guest), expanded=is_editing):
                if not is_editing:
                    # ── Read view ──────────────────────────────────────────
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Age", f"{pet.age} yr{'s' if pet.age != 1 else ''}")
                    col2.metric("Check-in", guest.check_in.strftime("%b %d"))
                    col3.metric("Check-out", guest.check_out.strftime("%b %d"))
                    col4.metric("Tasks", len(pet.tasks))

                    _toxic_meds, _safe_meds, _dangerous = _pet_flags(pet, guest.special_instructions)
                    if _toxic_meds:
                        for _med in _toxic_meds:
                            st.error(f"🚨 TOXIC MED — {_med}")
                    if _safe_meds:
                        for _med in _safe_meds:
                            st.error(f"💊 Medication: {_med}")
                    if pet.dietary_restrictions:
                        st.warning(f"🥗 Diet: {', '.join(pet.dietary_restrictions)}")
                    if _dangerous:
                        for _issue in _dangerous:
                            st.error(f"⚠️ DANGEROUS INSTRUCTION: '{_issue}' found in notes/instructions — do not follow without vet confirmation")
                    if pet.additional_information:
                        st.info(f"Notes: {', '.join(pet.additional_information)}")
                    if guest.special_instructions:
                        st.info(f"Special instructions: {guest.special_instructions}")
                    st.caption(f"Owner contact: {guest.owner_phone}")

                    _rb1, _rb2 = st.columns(2)
                    with _rb1:
                        if st.button("Edit Info", key=f"edit_btn_{gkey}"):
                            st.session_state.editing_pet = gkey
                            st.session_state[f"edit_meds_{gkey}"] = list(pet.medication_information)
                            st.session_state[f"edit_med_key_{gkey}"] = 0
                            st.rerun()
                    with _rb2:
                        if st.button(f"Check Out {pet.name}", key=f"checkout_{gkey}"):
                            hotel.check_out(pet.name)
                            logger.info("Checked out %s", pet.name)
                            st.success(f"{pet.name} has been checked out.")
                            st.rerun()

                else:
                    # ── Edit view ──────────────────────────────────────────
                    st.markdown("**Edit Pet Information**")
                    _ec1, _ec2 = st.columns(2)
                    with _ec1:
                        edit_age = st.number_input(
                            "Age (years)", min_value=0, max_value=50, step=1,
                            value=pet.age, key=f"edit_age_{gkey}",
                        )
                    with _ec2:
                        edit_breed = st.text_input(
                            "Breed", value=pet.breed, key=f"edit_breed_{gkey}",
                        )

                    edit_diet = st.text_input(
                        "Dietary restrictions (comma-separated)",
                        value=", ".join(pet.dietary_restrictions),
                        key=f"edit_diet_{gkey}",
                    )

                    st.markdown("**Medications**")
                    _emk = st.session_state[f"edit_med_key_{gkey}"]
                    for _mi, _med in enumerate(st.session_state[f"edit_meds_{gkey}"]):
                        _mc1, _mc2 = st.columns([8, 1])
                        _mc1.write(f"• {_med}")
                        if _mc2.button("✕", key=f"edit_rm_med_{gkey}_{_mi}"):
                            st.session_state[f"edit_meds_{gkey}"].pop(_mi)
                            st.rerun()

                    _nc1, _nc2, _nc3 = st.columns(3)
                    with _nc1:
                        _enew_name = st.text_input("Medication name", key=f"edit_new_name_{gkey}_{_emk}")
                    with _nc2:
                        _enew_freq = st.selectbox("Frequency", _FREQ_OPTIONS, key=f"edit_new_freq_{gkey}_{_emk}")
                    with _nc3:
                        _enew_method = st.selectbox("Administration", _ADMIN_METHODS, key=f"edit_new_method_{gkey}_{_emk}")
                    if _enew_method == "Other":
                        _enew_custom = st.text_input(
                            "How should it be administered?",
                            key=f"edit_new_custom_{gkey}_{_emk}",
                        )
                    else:
                        _enew_custom = ""
                    if st.button("Add Medication", key=f"edit_add_med_{gkey}",
                                 disabled=not _enew_name.strip()):
                        _m = _enew_custom.strip() if _enew_method == "Other" and _enew_custom.strip() else _enew_method
                        st.session_state[f"edit_meds_{gkey}"].append(
                            f"{_enew_name.strip()} — {_enew_freq} — {_m}"
                        )
                        st.session_state[f"edit_med_key_{gkey}"] += 1
                        st.rerun()

                    edit_notes = st.text_input(
                        "Additional notes (comma-separated)",
                        value=", ".join(pet.additional_information),
                        key=f"edit_notes_{gkey}",
                    )
                    edit_special = st.text_area(
                        "Special instructions", value=guest.special_instructions,
                        height=80, key=f"edit_special_{gkey}",
                    )

                    st.markdown("**Owner & Stay**")
                    _oc1, _oc2 = st.columns(2)
                    with _oc1:
                        edit_phone = st.text_input(
                            "Owner phone", value=guest.owner_phone, key=f"edit_phone_{gkey}",
                        )
                    with _oc2:
                        edit_checkout = st.date_input(
                            "Check-out date", value=guest.check_out, key=f"edit_checkout_{gkey}",
                        )

                    _sb1, _sb2 = st.columns(2)
                    with _sb1:
                        if st.button("Save Changes", type="primary", key=f"save_{gkey}"):
                            pet.age = int(edit_age)
                            pet.breed = edit_breed.strip()
                            pet.dietary_restrictions = _parse_csv(edit_diet)
                            pet.medication_information = list(st.session_state[f"edit_meds_{gkey}"])
                            pet.additional_information = _parse_csv(edit_notes)
                            guest.special_instructions = edit_special.strip()
                            guest.owner_phone = edit_phone.strip()
                            guest.check_out = edit_checkout
                            st.session_state.editing_pet = None
                            logger.info("Updated info for %s", pet.name)
                            st.success(f"{pet.name}'s information has been updated.")
                            st.rerun()
                    with _sb2:
                        if st.button("Cancel", key=f"cancel_{gkey}"):
                            st.session_state.editing_pet = None
                            st.rerun()

# ===========================================================================
# TAB 3 — AI SCHEDULE
# ===========================================================================
with tab_ai_schedule:
    st.subheader("AI-Generated Daily Schedule")
    st.markdown(
        "Click **Generate** to build a full care schedule for all current guests. "
        "Groq retrieves relevant guidelines from the pet care knowledge base "
        "and uses them to create a time-blocked schedule tailored to each animal."
    )

    sched_date = st.date_input("Schedule date", value=date.today(), key="ai_sched_date")
    guests_on_date = hotel.get_current_guests(sched_date)

    if not guests_on_date:
        st.info("No guests checked in for this date. Check in pets first.")
    else:
        st.caption(
            f"{len(guests_on_date)} guest(s) on {sched_date}: "
            + ", ".join(g.pet.name for g in guests_on_date)
        )

        additional_info = st.text_area(
            "Additional notes for today (optional)",
            placeholder=(
                "Add any context that should influence today's schedule — e.g. "
                "'Bella is nervous around loud noises today', "
                "'staff is short-handed this afternoon', "
                "'the outdoor play area is closed for cleaning until 2 PM', "
                "'Max had loose stool this morning — monitor closely'."
            ),
            height=100,
            key="ai_additional_info",
        )

        generate_btn = st.button(
            "Generate AI Schedule",
            type="primary",
            disabled=not bool(os.environ.get("GROQ_API_KEY")),
        )

        if not os.environ.get("GROQ_API_KEY"):
            st.warning(
                "Set the `GROQ_API_KEY` environment variable to enable AI scheduling. "
                "Run: `export GROQ_API_KEY=your_key_here`"
            )

        rag_result = get_rag_engine()
        if isinstance(rag_result, Exception):
            st.error(f"Knowledge base failed to load: {rag_result}. Check the knowledge_base/ folder.")

        if generate_btn:
            generator = get_generator()
            if generator is None:
                if isinstance(rag_result, Exception):
                    st.error("Cannot generate schedule — knowledge base failed to load (see error above).")
                else:
                    st.error("Could not initialize schedule generator. Check your API key.")
            else:
                with st.spinner("Retrieving care guidelines and generating schedule..."):
                    try:
                        result = generator.generate(hotel, sched_date,
                                                    additional_info=additional_info.strip() or None)
                        st.session_state.ai_result = result
                        logger.info(
                            "Schedule generated for %d pets", result["pet_count"]
                        )
                    except Exception as exc:
                        st.error(f"Error generating schedule: {exc}")
                        logger.error("Schedule generation failed: %s", exc)

        # Display last result
        result = st.session_state.ai_result
        if result:
            # Operational alerts (age, safe medications)
            if result.get("warnings"):
                st.subheader("Staff Alerts")
                for w in result["warnings"]:
                    if w.startswith("MEDICATION"):
                        st.error(w)
                    else:
                        st.warning(w)

            # Schedule
            st.subheader("Daily Schedule")
            st.markdown(result["schedule"])

            # RAG context transparency
            if result.get("context"):
                with st.expander(
                    f"Retrieved Guidelines ({len(result['context'])} chunks)", expanded=False
                ):
                    st.caption(
                        "These are the knowledge base excerpts Groq used to build this schedule."
                    )
                    for chunk in result["context"]:
                        st.markdown(
                            f"**Source:** `{chunk['source']}` "
                            f"(similarity distance: {chunk['distance']:.3f})"
                        )
                        st.text(chunk["text"])
                        st.divider()

            # Toxic medication flags — shown at the bottom, separate from operational alerts
            if result.get("toxic_flags"):
                st.divider()
                st.subheader("⚠ Flagged Toxic Medications")
                st.caption(
                    "The following substances reported by the owner are toxic to this animal. "
                    "They have been excluded from the schedule. "
                    "Contact the owner and their veterinarian before taking any action."
                )
                for flag in result["toxic_flags"]:
                    st.error(flag)

# ===========================================================================
# TAB 4 — MANUAL TASKS
# ===========================================================================
with tab_manual:
    st.subheader("Manual Task Management")
    st.caption("Add, view, and manage tasks for individual guests.")

    all_guests = hotel.get_all_guests()
    if not all_guests:
        st.info("No guests checked in yet.")
    else:
        pet_names = [g.pet.name for g in all_guests]

        # --- Add task -------------------------------------------------
        with st.expander("Add Task to a Guest", expanded=False):
            with st.form("add_task_form"):
                tc1, tc2, tc3, tc4, tc5, tc6 = st.columns(6)
                with tc1:
                    task_pet = st.selectbox("Pet", pet_names)
                with tc2:
                    task_desc = st.text_input("Description")
                with tc3:
                    task_time = st.text_input("Start (HH:MM)")
                with tc4:
                    task_duration = st.text_input("Duration (H:MM)")
                with tc5:
                    task_freq = st.selectbox(
                        "Frequency", ["daily", "weekly", "monthly", "yearly"]
                    )
                with tc6:
                    task_priority = st.selectbox(
                        "Priority", [1, 2, 3], index=1,
                        format_func=lambda x: {1: "High", 2: "Med", 3: "Low"}[x],
                    )
                add_task_btn = st.form_submit_button("Add Task")

            if add_task_btn:
                if not task_desc.strip():
                    st.warning("Task description is required.")
                else:
                    guest = hotel.get_guest_by_pet(task_pet)
                    if guest:
                        if any(
                            t.description.lower() == task_desc.lower()
                            for t in guest.pet.tasks
                        ):
                            st.warning(f"'{task_desc}' already exists for {task_pet}.")
                        else:
                            guest.pet.add_task(Task(
                                description=task_desc.strip(),
                                time=task_time,
                                duration=task_duration,
                                frequency=task_freq,
                                priority=task_priority,
                            ))
                            _task_dangerous = find_toxic_instructions(
                                guest.pet.species, task_desc
                            )
                            _task_injection = [
                                p for p in _INJECTION_PATTERNS if p in task_desc.lower()
                            ]
                            if _task_dangerous:
                                for _issue in _task_dangerous:
                                    st.error(
                                        f"⚠️ DANGEROUS CONTENT in task description: "
                                        f"'{_issue}' is harmful to {guest.pet.species}s. "
                                        "Task saved but verify before following."
                                    )
                            if _task_injection:
                                for _pat in _task_injection:
                                    st.error(
                                        f"⚠️ SUSPICIOUS CONTENT in task description: "
                                        f"'{_pat}' looks like a prompt injection attempt."
                                    )
                            if not _task_dangerous and not _task_injection:
                                st.success(f"Task added to {task_pet}.")
                            st.rerun()

        # --- Task list ------------------------------------------------
        st.markdown("**Task List**")
        filter_pet = st.selectbox("Filter by pet", ["All guests"] + pet_names,
                                  key="manual_filter_pet")
        filter_status = st.selectbox(
            "Filter by status", ["All", "Pending", "Completed"],
            key="manual_filter_status",
        )

        display_guests = (
            all_guests if filter_pet == "All guests"
            else [g for g in all_guests if g.pet.name == filter_pet]
        )

        all_tasks_flat: list[tuple[Pet, Task]] = []
        for g in display_guests:
            for t in g.pet.tasks:
                if filter_status == "All":
                    all_tasks_flat.append((g.pet, t))
                elif filter_status == "Pending" and not t.is_completed:
                    all_tasks_flat.append((g.pet, t))
                elif filter_status == "Completed" and t.is_completed:
                    all_tasks_flat.append((g.pet, t))

        if not all_tasks_flat:
            st.info("No tasks match the current filters.")
        else:
            priority_badge = {1: "🔴 High", 2: "🟡 Med", 3: "🟢 Low"}
            header = st.columns([1, 3, 1, 1, 1, 1, 1, 1])
            for col, label in zip(
                header, ["Done", "Description", "Pet", "Time",
                         "Duration", "Frequency", "Priority", "Delete"]
            ):
                col.markdown(f"**{label}**")

            for i, (pet, task) in enumerate(all_tasks_flat):
                cols = st.columns([1, 3, 1, 1, 1, 1, 1, 1])
                checked = cols[0].checkbox("", value=task.is_completed,
                                           key=f"done_{id(task)}_{i}")
                if checked and not task.is_completed:
                    task.is_completed = True
                    st.rerun()
                elif not checked and task.is_completed:
                    task.is_completed = False
                    st.rerun()
                cols[1].write(task.description)
                cols[2].write(pet.name)
                cols[3].write(task.time or "—")
                cols[4].write(task.duration or "—")
                cols[5].write(task.frequency.capitalize())
                cols[6].write(priority_badge.get(task.priority, str(task.priority)))
                if cols[7].button("🗑️", key=f"del_{id(task)}_{i}"):
                    pet.remove_task(task.description)
                    st.rerun()

# ---------------------------------------------------------------------------
# Persist hotel state on every rerun so data survives browser refresh
# ---------------------------------------------------------------------------
hotel.save()

