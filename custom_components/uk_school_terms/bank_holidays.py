"""Replaceable static bank-holiday provider for the MVP."""

from __future__ import annotations

from datetime import date

# England and Wales dates covering the bundled sample academic years.
_ENGLAND_WALES_BANK_HOLIDAYS = {
    date(2025, 1, 1),
    date(2025, 4, 18),
    date(2025, 4, 21),
    date(2025, 5, 5),
    date(2025, 5, 26),
    date(2025, 8, 25),
    date(2025, 12, 25),
    date(2025, 12, 26),
    date(2026, 1, 1),
    date(2026, 4, 3),
    date(2026, 4, 6),
    date(2026, 5, 4),
    date(2026, 5, 25),
    date(2026, 8, 31),
    date(2026, 12, 25),
    date(2026, 12, 28),
}


def get_bank_holidays(country: str, year: int) -> set[date]:
    """Return static bank holidays for a country and calendar year."""
    if country != "england":
        return set()
    return {
        holiday
        for holiday in _ENGLAND_WALES_BANK_HOLIDAYS
        if holiday.year == year
    }

