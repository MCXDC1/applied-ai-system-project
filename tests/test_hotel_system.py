import pytest
from datetime import date, timedelta

from hotel_system import Hotel, HotelGuest
from pawpal_system import Pet


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_pet(name="Buddy", species="dog", breed="Labrador", age=3):
    return Pet(name=name, species=species, age=age, breed=breed)


def make_guest(pet=None, check_in=None, check_out=None, owner="Alex", phone="555-0100"):
    today = date.today()
    return HotelGuest(
        pet=pet or make_pet(),
        owner_name=owner,
        owner_phone=phone,
        check_in=check_in or today,
        check_out=check_out or today + timedelta(days=3),
    )


# ---------------------------------------------------------------------------
# HotelGuest.is_current
# ---------------------------------------------------------------------------

def test_is_current_on_check_in_day():
    today = date.today()
    guest = make_guest(check_in=today, check_out=today + timedelta(days=2))
    assert guest.is_current(today) is True


def test_is_current_on_check_out_day():
    today = date.today()
    guest = make_guest(check_in=today - timedelta(days=2), check_out=today)
    assert guest.is_current(today) is True


def test_is_current_between_dates():
    today = date.today()
    guest = make_guest(check_in=today - timedelta(days=1), check_out=today + timedelta(days=1))
    assert guest.is_current(today) is True


def test_is_not_current_before_check_in():
    today = date.today()
    guest = make_guest(check_in=today + timedelta(days=1), check_out=today + timedelta(days=3))
    assert guest.is_current(today) is False


def test_is_not_current_after_check_out():
    today = date.today()
    guest = make_guest(check_in=today - timedelta(days=3), check_out=today - timedelta(days=1))
    assert guest.is_current(today) is False


# ---------------------------------------------------------------------------
# HotelGuest.summary
# ---------------------------------------------------------------------------

def test_summary_contains_pet_name():
    pet = make_pet(name="Fluffy")
    guest = make_guest(pet=pet)
    assert "Fluffy" in guest.summary()


def test_summary_contains_owner_name():
    guest = make_guest(owner="Jordan")
    assert "Jordan" in guest.summary()


# ---------------------------------------------------------------------------
# Hotel.check_in
# ---------------------------------------------------------------------------

def test_check_in_adds_guest():
    hotel = Hotel()
    hotel.check_in(make_guest())
    assert hotel.guest_count() == 1


def test_check_in_duplicate_name_raises():
    hotel = Hotel()
    hotel.check_in(make_guest(pet=make_pet(name="Buddy")))
    with pytest.raises(ValueError):
        hotel.check_in(make_guest(pet=make_pet(name="Buddy")))


def test_check_in_case_insensitive_duplicate():
    hotel = Hotel()
    hotel.check_in(make_guest(pet=make_pet(name="buddy")))
    with pytest.raises(ValueError):
        hotel.check_in(make_guest(pet=make_pet(name="BUDDY")))


def test_check_in_different_names_allowed():
    hotel = Hotel()
    hotel.check_in(make_guest(pet=make_pet(name="Buddy")))
    hotel.check_in(make_guest(pet=make_pet(name="Max")))
    assert len(hotel.get_all_guests()) == 2


# ---------------------------------------------------------------------------
# Hotel.check_out
# ---------------------------------------------------------------------------

def test_check_out_removes_guest():
    hotel = Hotel()
    hotel.check_in(make_guest(pet=make_pet(name="Buddy")))
    removed = hotel.check_out("Buddy")
    assert removed is not None
    assert hotel.guest_count() == 0


def test_check_out_returns_guest():
    hotel = Hotel()
    pet = make_pet(name="Buddy")
    hotel.check_in(make_guest(pet=pet))
    removed = hotel.check_out("Buddy")
    assert removed.pet.name == "Buddy"


def test_check_out_unknown_returns_none():
    hotel = Hotel()
    result = hotel.check_out("Ghost")
    assert result is None


def test_check_out_case_insensitive():
    hotel = Hotel()
    hotel.check_in(make_guest(pet=make_pet(name="Buddy")))
    removed = hotel.check_out("buddy")
    assert removed is not None


# ---------------------------------------------------------------------------
# Hotel.get_current_guests
# ---------------------------------------------------------------------------

def test_get_current_guests_filters_by_date():
    today = date.today()
    hotel = Hotel()
    current_pet = make_pet(name="Current")
    past_pet = make_pet(name="Past")
    hotel.check_in(make_guest(pet=current_pet, check_in=today, check_out=today + timedelta(days=1)))
    hotel.check_in(make_guest(pet=past_pet, check_in=today - timedelta(days=5), check_out=today - timedelta(days=1)))
    current = hotel.get_current_guests(today)
    names = [g.pet.name for g in current]
    assert "Current" in names
    assert "Past" not in names


def test_get_current_guests_empty_hotel():
    hotel = Hotel()
    assert hotel.get_current_guests() == []


# ---------------------------------------------------------------------------
# Hotel.guest_count
# ---------------------------------------------------------------------------

def test_guest_count_zero_on_empty_hotel():
    assert Hotel().guest_count() == 0


def test_guest_count_matches_checked_in():
    hotel = Hotel()
    hotel.check_in(make_guest(pet=make_pet(name="A")))
    hotel.check_in(make_guest(pet=make_pet(name="B")))
    assert hotel.guest_count() == 2


# ---------------------------------------------------------------------------
# Hotel.species_breakdown
# ---------------------------------------------------------------------------

def test_species_breakdown_single_species():
    hotel = Hotel()
    hotel.check_in(make_guest(pet=make_pet(name="A", species="dog")))
    hotel.check_in(make_guest(pet=make_pet(name="B", species="dog")))
    breakdown = hotel.species_breakdown()
    assert breakdown == {"dog": 2}


def test_species_breakdown_mixed_species():
    hotel = Hotel()
    hotel.check_in(make_guest(pet=make_pet(name="A", species="dog")))
    hotel.check_in(make_guest(pet=make_pet(name="B", species="cat")))
    breakdown = hotel.species_breakdown()
    assert breakdown["dog"] == 1
    assert breakdown["cat"] == 1


def test_species_breakdown_empty():
    assert Hotel().species_breakdown() == {}


# ---------------------------------------------------------------------------
# Hotel.get_guest_by_pet
# ---------------------------------------------------------------------------

def test_get_guest_by_pet_found():
    hotel = Hotel()
    hotel.check_in(make_guest(pet=make_pet(name="Buddy")))
    guest = hotel.get_guest_by_pet("Buddy")
    assert guest is not None
    assert guest.pet.name == "Buddy"


def test_get_guest_by_pet_not_found():
    hotel = Hotel()
    assert hotel.get_guest_by_pet("Ghost") is None


def test_get_guest_by_pet_case_insensitive():
    hotel = Hotel()
    hotel.check_in(make_guest(pet=make_pet(name="Buddy")))
    assert hotel.get_guest_by_pet("buddy") is not None


# ---------------------------------------------------------------------------
# Hotel.get_all_guests
# ---------------------------------------------------------------------------

def test_get_all_guests_includes_past_guests():
    today = date.today()
    hotel = Hotel()
    hotel.check_in(make_guest(pet=make_pet(name="Past"), check_in=today - timedelta(days=5), check_out=today - timedelta(days=1)))
    assert len(hotel.get_all_guests()) == 1
