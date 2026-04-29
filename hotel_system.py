import json
import logging
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from pawpal_system import Pet

logger = logging.getLogger(__name__)


@dataclass
class HotelGuest:
    """A single pet currently or previously checked in to the hotel."""
    pet: Pet
    owner_name: str
    owner_phone: str
    check_in: date
    check_out: date
    special_instructions: str = ""

    def is_current(self, reference_date: date = None) -> bool:
        d = reference_date or date.today()
        return self.check_in <= d <= self.check_out

    def summary(self) -> str:
        return (
            f"{self.pet.name} ({self.pet.species}, {self.pet.breed}, age {self.pet.age}) "
            f"— Owner: {self.owner_name} | {self.check_in} → {self.check_out}"
        )

    def to_dict(self) -> dict:
        return {
            "pet": self.pet.to_dict(),
            "owner_name": self.owner_name,
            "owner_phone": self.owner_phone,
            "check_in": self.check_in.isoformat(),
            "check_out": self.check_out.isoformat(),
            "special_instructions": self.special_instructions,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "HotelGuest":
        return cls(
            pet=Pet.from_dict(d["pet"]),
            owner_name=d["owner_name"],
            owner_phone=d["owner_phone"],
            check_in=date.fromisoformat(d["check_in"]),
            check_out=date.fromisoformat(d["check_out"]),
            special_instructions=d.get("special_instructions", ""),
        )


class Hotel:
    """Manages all pet guests checked in to the hotel."""

    def __init__(self, name: str = "PawPal Hotel",
                 open_time: str = "07:00",
                 close_time: str = "20:00"):
        self.name = name
        self.open_time = open_time
        self.close_time = close_time
        self._guests: list[HotelGuest] = []

    # ------------------------------------------------------------------
    # Guest management
    # ------------------------------------------------------------------

    def check_in(self, guest: HotelGuest) -> None:
        duplicate = next(
            (g for g in self._guests
             if g.pet.name.lower() == guest.pet.name.lower()
             and g.owner_phone == guest.owner_phone),
            None,
        )
        if duplicate:
            raise ValueError(
                f"'{guest.pet.name}' is already checked in under phone {guest.owner_phone}."
            )
        self._guests.append(guest)
        logger.info("Checked in: %s", guest.summary())

    def check_out(self, pet_name: str) -> HotelGuest | None:
        for i, g in enumerate(self._guests):
            if g.pet.name.lower() == pet_name.lower():
                removed = self._guests.pop(i)
                logger.info("Checked out: %s", removed.summary())
                return removed
        logger.warning("Check-out requested for unknown pet: %s", pet_name)
        return None

    def remove_guest(self, pet_name: str) -> None:
        self._guests = [g for g in self._guests if g.pet.name.lower() != pet_name.lower()]

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_current_guests(self, reference_date: date = None) -> list[HotelGuest]:
        d = reference_date or date.today()
        return [g for g in self._guests if g.is_current(d)]

    def get_all_guests(self) -> list[HotelGuest]:
        return list(self._guests)

    def get_guest_by_pet(self, pet_name: str) -> HotelGuest | None:
        for g in self._guests:
            if g.pet.name.lower() == pet_name.lower():
                return g
        return None

    def guest_count(self, reference_date: date = None) -> int:
        return len(self.get_current_guests(reference_date))

    def species_breakdown(self, reference_date: date = None) -> dict[str, int]:
        breakdown: dict[str, int] = {}
        for g in self.get_current_guests(reference_date):
            key = g.pet.species.lower()
            breakdown[key] = breakdown.get(key, 0) + 1
        return breakdown

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, path: str | Path = "hotel_state.json") -> None:
        data = {
            "name": self.name,
            "open_time": self.open_time,
            "close_time": self.close_time,
            "guests": [g.to_dict() for g in self._guests],
        }
        Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")
        logger.debug("Hotel state saved to %s (%d guests)", path, len(self._guests))

    @classmethod
    def load(cls, path: str | Path = "hotel_state.json") -> "Hotel":
        p = Path(path)
        if not p.exists():
            return cls()
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            hotel = cls(
                name=data.get("name", "PawPal Hotel"),
                open_time=data.get("open_time", "07:00"),
                close_time=data.get("close_time", "20:00"),
            )
            hotel._guests = [HotelGuest.from_dict(g) for g in data.get("guests", [])]
            logger.info("Hotel state loaded from %s (%d guests)", path, len(hotel._guests))
            return hotel
        except Exception as exc:
            logger.error("Failed to load hotel state from %s: %s", path, exc)
            return cls()
