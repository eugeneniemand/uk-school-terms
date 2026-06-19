"""Constants for UK School Terms."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "uk_school_terms"
PLATFORMS: Final = ["binary_sensor", "sensor", "calendar"]

CONF_COUNTRY: Final = "country"
CONF_COUNCIL: Final = "council"
CONF_SCHOOL_NAME: Final = "school_name"
CONF_INSET_DAYS: Final = "inset_days"
CONF_CLOSURE_DAYS: Final = "closure_days"
CONF_EXCLUDE_BANK_HOLIDAYS: Final = "exclude_bank_holidays"

DEFAULT_COUNTRY: Final = "england"
DEFAULT_EXCLUDE_BANK_HOLIDAYS: Final = True

DATA_COORDINATOR: Final = "coordinator"

