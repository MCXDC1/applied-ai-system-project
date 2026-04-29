import os
import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

from hotel_system import Hotel, HotelGuest
from pawpal_system import Pet
from schedule_generator import HotelScheduleGenerator, TOXIC_MEDICATIONS, find_toxic_instructions


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_pet(name="Buddy", species="dog", breed="Labrador", age=3,
             medications=None, notes=None, diet=None):
    return Pet(
        name=name, species=species, age=age, breed=breed,
        dietary_restrictions=diet or [],
        medication_information=medications or [],
        additional_information=notes or [],
    )


def make_guest(pet, owner="Alex", phone="555-0100", days=2):
    today = date.today()
    return HotelGuest(
        pet=pet,
        owner_name=owner,
        owner_phone=phone,
        check_in=today,
        check_out=today + timedelta(days=days),
    )


def make_hotel_with(*pets):
    hotel = Hotel()
    for pet in pets:
        hotel.check_in(make_guest(pet))
    return hotel


@pytest.fixture
def mock_rag():
    rag = MagicMock()
    rag.retrieve_for_pet.return_value = [
        {"text": "Dogs need daily walks.", "source": "dog_care.md", "distance": 0.1}
    ]
    return rag


@pytest.fixture
def generator(mock_rag, monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    with patch("schedule_generator.Groq"):
        gen = HotelScheduleGenerator(mock_rag)
    return gen


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

def test_missing_api_key_raises(mock_rag, monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(EnvironmentError, match="GROQ_API_KEY"):
        HotelScheduleGenerator(mock_rag)


# ---------------------------------------------------------------------------
# generate — return structure
# ---------------------------------------------------------------------------

def test_generate_no_guests_returns_empty_message(generator):
    hotel = Hotel()
    result = generator.generate(hotel, target_date=date.today())
    assert result["pet_count"] == 0
    assert result["schedule"] == "No pets are currently checked in for this date."
    assert result["context"] == []
    assert result["warnings"] == []


def test_generate_returns_required_keys(generator):
    hotel = make_hotel_with(make_pet())
    generator._client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="08:00 | Walk | Buddy | —"))]
    )
    result = generator.generate(hotel)
    assert set(result.keys()) == {"schedule", "context", "pet_count", "warnings", "toxic_flags"}


def test_generate_pet_count_matches_guests(generator):
    hotel = make_hotel_with(make_pet("A"), make_pet("B"))
    generator._client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="schedule text"))]
    )
    result = generator.generate(hotel)
    assert result["pet_count"] == 2


def test_generate_returns_groq_text(generator):
    hotel = make_hotel_with(make_pet())
    generator._client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="My generated schedule"))]
    )
    result = generator.generate(hotel)
    assert result["schedule"] == "My generated schedule"


# ---------------------------------------------------------------------------
# generate — guardrail warnings
# ---------------------------------------------------------------------------

def test_medication_alert_added(generator):
    pet = make_pet(medications=["insulin"])
    hotel = make_hotel_with(pet)
    generator._client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="schedule"))]
    )
    result = generator.generate(hotel)
    assert any("MEDICATION ALERT" in w for w in result["warnings"])


def test_young_animal_warning_added(generator):
    pet = make_pet(age=0)
    hotel = make_hotel_with(pet)
    generator._client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="schedule"))]
    )
    result = generator.generate(hotel)
    assert any("YOUNG ANIMAL" in w for w in result["warnings"])


def test_senior_dog_warning_added(generator):
    pet = make_pet(age=8, species="dog")
    hotel = make_hotel_with(pet)
    generator._client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="schedule"))]
    )
    result = generator.generate(hotel)
    assert any("SENIOR PET" in w for w in result["warnings"])


def test_senior_cat_warning_added(generator):
    pet = make_pet(name="Mittens", age=11, species="cat", breed="Siamese")
    hotel = make_hotel_with(pet)
    generator._client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="schedule"))]
    )
    result = generator.generate(hotel)
    assert any("SENIOR PET" in w for w in result["warnings"])


def test_no_warnings_for_healthy_adult_pet(generator):
    pet = make_pet(age=3)
    hotel = make_hotel_with(pet)
    generator._client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="schedule"))]
    )
    result = generator.generate(hotel)
    assert result["warnings"] == []


def test_multiple_warnings_for_medicated_senior(generator):
    pet = make_pet(age=9, species="dog", medications=["prednisone"])
    hotel = make_hotel_with(pet)
    generator._client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="schedule"))]
    )
    result = generator.generate(hotel)
    assert len(result["warnings"]) == 2


# ---------------------------------------------------------------------------
# generate — RAG context
# ---------------------------------------------------------------------------

def test_generate_context_includes_rag_chunks(generator, mock_rag):
    pet = make_pet()
    hotel = make_hotel_with(pet)
    generator._client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="schedule"))]
    )
    result = generator.generate(hotel)
    assert len(result["context"]) > 0
    assert result["context"][0]["source"] == "dog_care.md"


def test_generate_deduplicates_rag_chunks(generator, mock_rag):
    # Two pets returning the same chunk should deduplicate
    mock_rag.retrieve_for_pet.return_value = [
        {"text": "Dogs need daily walks.", "source": "dog_care.md", "distance": 0.1}
    ]
    hotel = make_hotel_with(make_pet("A"), make_pet("B"))
    generator._client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="schedule"))]
    )
    result = generator.generate(hotel)
    assert len(result["context"]) == 1


# ---------------------------------------------------------------------------
# Toxic medication safeguards — _find_toxic_meds (unit tests, no API call)
# ---------------------------------------------------------------------------

def test_find_toxic_meds_ibuprofen_dog():
    meds = ["Ibuprofen 400mg — Once daily — In food"]
    assert HotelScheduleGenerator._find_toxic_meds("dog", meds) == meds


def test_find_toxic_meds_advil_dog():
    meds = ["Advil — Twice daily — Oral"]
    assert HotelScheduleGenerator._find_toxic_meds("dog", meds) == meds


def test_find_toxic_meds_tylenol_cat():
    meds = ["Tylenol 500mg — Once daily — In food"]
    assert HotelScheduleGenerator._find_toxic_meds("cat", meds) == meds


def test_find_toxic_meds_acetaminophen_cat():
    meds = ["Acetaminophen — As needed — Oral"]
    assert HotelScheduleGenerator._find_toxic_meds("cat", meds) == meds


def test_find_toxic_meds_aspirin_cat():
    meds = ["Aspirin — Once daily — In food"]
    assert HotelScheduleGenerator._find_toxic_meds("cat", meds) == meds


def test_find_toxic_meds_aspirin_not_toxic_for_dog():
    # Aspirin is NOT in the dog toxic list (sometimes vet-prescribed)
    meds = ["Aspirin — Once daily — In food"]
    assert HotelScheduleGenerator._find_toxic_meds("dog", meds) == []


def test_find_toxic_meds_safe_medication_not_flagged():
    meds = ["Prednisone 5mg — Once daily — In food"]
    assert HotelScheduleGenerator._find_toxic_meds("dog", meds) == []


def test_find_toxic_meds_mixed_returns_only_toxic():
    meds = [
        "Prednisone 5mg — Once daily — In food",
        "Ibuprofen 400mg — Twice daily — In food",
        "Amoxicillin — Twice daily — Oral",
    ]
    result = HotelScheduleGenerator._find_toxic_meds("dog", meds)
    assert len(result) == 1
    assert "Ibuprofen" in result[0]


def test_find_toxic_meds_case_insensitive():
    meds = ["IBUPROFEN 200mg — Once daily — In food"]
    assert HotelScheduleGenerator._find_toxic_meds("dog", meds) != []


def test_find_toxic_meds_unknown_species_returns_empty():
    meds = ["Ibuprofen 400mg — Once daily — In food"]
    assert HotelScheduleGenerator._find_toxic_meds("hamster", meds) == []


def test_find_toxic_meds_empty_medications():
    assert HotelScheduleGenerator._find_toxic_meds("dog", []) == []


# ---------------------------------------------------------------------------
# Toxic medication safeguards — generate() integration (mocked API)
# ---------------------------------------------------------------------------

def test_toxic_dog_med_produces_toxic_warning(generator):
    pet = make_pet(medications=["Ibuprofen 400mg — Once daily — In food"])
    hotel = make_hotel_with(pet)
    generator._client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="08:00 | Walk | Buddy | —"))]
    )
    result = generator.generate(hotel)
    assert any("TOXIC MEDICATION" in w for w in result["toxic_flags"])
    assert not any("TOXIC MEDICATION" in w for w in result["warnings"])


def test_toxic_cat_med_produces_toxic_warning(generator):
    pet = make_pet(name="Mittens", species="cat", breed="Siamese",
                   medications=["Acetaminophen — Once daily — In food"])
    hotel = make_hotel_with(pet)
    generator._client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="08:00 | Feed | Mittens | —"))]
    )
    result = generator.generate(hotel)
    assert any("TOXIC MEDICATION" in w for w in result["toxic_flags"])
    assert not any("TOXIC MEDICATION" in w for w in result["warnings"])


def test_toxic_med_excluded_from_rag_query(generator, mock_rag):
    pet = make_pet(medications=["Ibuprofen 400mg — Once daily — In food"])
    hotel = make_hotel_with(pet)
    generator._client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="schedule"))]
    )
    generator.generate(hotel)
    medications_passed = mock_rag.retrieve_for_pet.call_args.kwargs["medications"]
    assert not any("ibuprofen" in m.lower() for m in medications_passed)


def test_toxic_med_excluded_safe_med_kept(generator, mock_rag):
    pet = make_pet(medications=[
        "Ibuprofen 400mg — Once daily — In food",
        "Prednisone 5mg — Once daily — In food",
    ])
    hotel = make_hotel_with(pet)
    generator._client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="schedule"))]
    )
    generator.generate(hotel)
    call_kwargs = mock_rag.retrieve_for_pet.call_args
    medications_passed = call_kwargs.kwargs.get("medications") or call_kwargs.args[4]
    assert not any("ibuprofen" in m.lower() for m in medications_passed)
    assert any("prednisone" in m.lower() for m in medications_passed)


def test_toxic_warning_names_the_substance(generator):
    pet = make_pet(medications=["Ibuprofen 400mg — Once daily — In food"])
    hotel = make_hotel_with(pet)
    generator._client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="08:00 | Walk | Buddy | —"))]
    )
    result = generator.generate(hotel)
    assert any("ibuprofen" in w.lower() for w in result["toxic_flags"])


def test_safe_medication_not_flagged_as_toxic(generator):
    pet = make_pet(medications=["Prednisone 5mg — Once daily — In food"])
    hotel = make_hotel_with(pet)
    generator._client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="schedule"))]
    )
    result = generator.generate(hotel)
    assert result["toxic_flags"] == []


# ---------------------------------------------------------------------------
# Toxic medication safeguards — _scan_output_for_toxics (post-processing)
# ---------------------------------------------------------------------------

def test_scan_output_catches_ibuprofen_mention():
    dog_guest = MagicMock()
    dog_guest.pet.species = "dog"
    schedule_text = "08:00 | Give ibuprofen | Buddy | as directed"
    warnings = HotelScheduleGenerator._scan_output_for_toxics(schedule_text, [dog_guest])
    assert any("ibuprofen" in w.lower() for w in warnings)
    assert any("SAFETY ALERT" in w for w in warnings)


def test_scan_output_catches_tylenol_mention_for_cat():
    cat_guest = MagicMock()
    cat_guest.pet.species = "cat"
    schedule_text = "Give Tylenol to Mittens as noted by owner"
    warnings = HotelScheduleGenerator._scan_output_for_toxics(schedule_text, [cat_guest])
    assert any("SAFETY ALERT" in w for w in warnings)


def test_scan_output_clean_schedule_no_warnings():
    dog_guest = MagicMock()
    dog_guest.pet.species = "dog"
    schedule_text = "08:00 | Walk | Buddy |\n09:00 | Feed | Buddy |"
    warnings = HotelScheduleGenerator._scan_output_for_toxics(schedule_text, [dog_guest])
    assert warnings == []


def test_scan_output_no_false_positive_on_safe_med():
    dog_guest = MagicMock()
    dog_guest.pet.species = "dog"
    schedule_text = "09:00 | Administer prednisone 5mg | Buddy | in food"
    warnings = HotelScheduleGenerator._scan_output_for_toxics(schedule_text, [dog_guest])
    assert warnings == []


def test_generate_adds_output_scan_warning_if_ai_mentions_toxic(generator):
    pet = make_pet(medications=["Prednisone 5mg — Once daily — In food"])
    hotel = make_hotel_with(pet)
    # AI hallucinates ibuprofen into its output despite our prompt
    generator._client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(
            content="09:00 | Give ibuprofen | Buddy | as noted"
        ))]
    )
    result = generator.generate(hotel)
    assert any("SAFETY ALERT" in w for w in result["toxic_flags"])
    assert not any("SAFETY ALERT" in w for w in result["warnings"])


# ---------------------------------------------------------------------------
# Dangerous instruction detection — find_toxic_instructions (unit tests)
# ---------------------------------------------------------------------------

def test_find_toxic_instructions_chocolate_dog():
    assert "chocolate" in find_toxic_instructions("dog", "feed the dog chocolate as a treat")


def test_find_toxic_instructions_grapes_dog():
    assert "grapes" in find_toxic_instructions("dog", "owner says dog loves grapes")


def test_find_toxic_instructions_lily_cat():
    assert "lily" in find_toxic_instructions("cat", "there is a lily on the table near the cat")


def test_find_toxic_instructions_no_food_pattern():
    assert "no food" in find_toxic_instructions("dog", "no food after 6pm")


def test_find_toxic_instructions_never_feed():
    assert "never feed" in find_toxic_instructions("dog", "never feed the dog from the table")


def test_find_toxic_instructions_outside_all_night():
    assert "outside all night" in find_toxic_instructions("cat", "keep the cat outside all night")


def test_find_toxic_instructions_do_not_feed():
    assert "do not feed" in find_toxic_instructions("dog", "do not feed between meals")


def test_find_toxic_instructions_safe_instruction_not_flagged():
    assert find_toxic_instructions("dog", "give the dog a walk at 8am and feed at 9am") == []


def test_find_toxic_instructions_empty_text():
    assert find_toxic_instructions("dog", "") == []


def test_find_toxic_instructions_case_insensitive():
    assert find_toxic_instructions("dog", "Feed the dog CHOCOLATE daily") != []


def test_find_toxic_instructions_unknown_species_ignores_foods():
    # No toxic foods defined for hamster, but dangerous patterns still apply
    result = find_toxic_instructions("hamster", "no food or water allowed")
    assert "no food" in result


def test_find_toxic_instructions_cat_avocado():
    assert "avocado" in find_toxic_instructions("cat", "mix avocado into cat food")


# ---------------------------------------------------------------------------
# Dangerous instruction detection — generate() integration
# ---------------------------------------------------------------------------

def test_generate_flags_chocolate_in_special_instructions(generator):
    pet = make_pet()
    hotel = Hotel()
    today = date.today()
    from datetime import timedelta
    guest = HotelGuest(
        pet=pet, owner_name="Alex", owner_phone="555-0100",
        check_in=today, check_out=today + timedelta(days=2),
        special_instructions="please give the dog some chocolate as a reward",
    )
    hotel.check_in(guest)
    generator._client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="schedule"))]
    )
    result = generator.generate(hotel)
    assert any("DANGEROUS INSTRUCTION" in w for w in result["toxic_flags"])
    assert any("chocolate" in w.lower() for w in result["toxic_flags"])


def test_generate_flags_dangerous_pattern_in_notes(generator):
    pet = make_pet(notes=["never feed between 6 and 8"])
    hotel = make_hotel_with(pet)
    generator._client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="schedule"))]
    )
    result = generator.generate(hotel)
    assert any("DANGEROUS INSTRUCTION" in w for w in result["toxic_flags"])


def test_generate_safe_instructions_not_flagged(generator):
    pet = make_pet(notes=["prefers walks in the morning"])
    hotel = make_hotel_with(pet)
    generator._client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="schedule"))]
    )
    result = generator.generate(hotel)
    assert not any("DANGEROUS INSTRUCTION" in w for w in result["toxic_flags"])


def test_generate_dangerous_instruction_not_in_warnings(generator):
    pet = make_pet()
    hotel = Hotel()
    today = date.today()
    from datetime import timedelta
    guest = HotelGuest(
        pet=pet, owner_name="Alex", owner_phone="555-0100",
        check_in=today, check_out=today + timedelta(days=2),
        special_instructions="feed the dog grapes for energy",
    )
    hotel.check_in(guest)
    generator._client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="schedule"))]
    )
    result = generator.generate(hotel)
    assert any("DANGEROUS INSTRUCTION" in w for w in result["toxic_flags"])
    assert not any("DANGEROUS INSTRUCTION" in w for w in result["warnings"])
