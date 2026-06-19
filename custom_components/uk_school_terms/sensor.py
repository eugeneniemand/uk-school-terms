"""Sensors for UK School Terms."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DATA_COORDINATOR, DOMAIN
from .coordinator import UKSchoolTermsCoordinator
from .entity import UKSchoolTermsEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    async_add_entities(
        [
            UKCurrentTermSensor(coordinator),
            UKNextEventSensor(coordinator),
            UKDaysUntilNextEventSensor(coordinator),
        ]
    )


class UKCurrentTermSensor(UKSchoolTermsEntity, SensorEntity):
    """Current term name."""

    _attr_translation_key = "current_term"

    def __init__(self, coordinator: UKSchoolTermsCoordinator) -> None:
        super().__init__(coordinator, "current_term")

    @property
    def native_value(self) -> str:
        status = self.coordinator.data["status"]
        if status.current_term and status.term_time:
            return status.current_term
        if status.academic_year:
            return "Holiday"
        return "Unknown"


class UKNextEventSensor(UKSchoolTermsEntity, SensorEntity):
    """Next term boundary."""

    _attr_translation_key = "next_event"

    def __init__(self, coordinator: UKSchoolTermsCoordinator) -> None:
        super().__init__(coordinator, "next_event")

    @property
    def native_value(self) -> str:
        event = self.coordinator.data["next_event"]
        return event.name if event else "Unknown"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        event = self.coordinator.data["next_event"]
        if event is None:
            return {}
        today = self.coordinator.data["date"]
        return {
            "event_type": event.event_type,
            "event_date": event.event_date.isoformat(),
            "days_until": (event.event_date - today).days,
            "academic_year": event.academic_year,
        }


class UKDaysUntilNextEventSensor(UKSchoolTermsEntity, SensorEntity):
    """Number of days until the next term boundary."""

    _attr_translation_key = "days_until_next_event"
    _attr_native_unit_of_measurement = UnitOfTime.DAYS
    _attr_suggested_display_precision = 0

    def __init__(self, coordinator: UKSchoolTermsCoordinator) -> None:
        super().__init__(coordinator, "days_until_next_event")

    @property
    def native_value(self) -> int | None:
        event = self.coordinator.data["next_event"]
        if event is None:
            return None
        return (event.event_date - self.coordinator.data["date"]).days

