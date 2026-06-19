"""Binary sensors for UK School Terms."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
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
    """Set up binary sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    async_add_entities(
        [
            UKSchoolDayBinarySensor(coordinator),
            UKTermTimeBinarySensor(coordinator),
        ]
    )


class UKSchoolDayBinarySensor(UKSchoolTermsEntity, BinarySensorEntity):
    """Whether today is a school day."""

    _attr_translation_key = "school_day"
    _attr_device_class = BinarySensorDeviceClass.RUNNING

    def __init__(self, coordinator: UKSchoolTermsCoordinator) -> None:
        super().__init__(coordinator, "school_day")

    @property
    def is_on(self) -> bool:
        return self.coordinator.data["status"].school_day

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        status = self.coordinator.data["status"]
        return {
            "council": self.coordinator.council.name,
            "country": self.coordinator.council.country,
            "academic_year": status.academic_year,
            "current_term": status.current_term,
            "reason": status.reason,
            "source_url": self.coordinator.council.source_url,
        }


class UKTermTimeBinarySensor(UKSchoolTermsEntity, BinarySensorEntity):
    """Whether today is inside a term and outside half-term."""

    _attr_translation_key = "term_time"

    def __init__(self, coordinator: UKSchoolTermsCoordinator) -> None:
        super().__init__(coordinator, "term_time")

    @property
    def is_on(self) -> bool:
        return self.coordinator.data["status"].term_time

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        status = self.coordinator.data["status"]
        return {
            "council": self.coordinator.council.name,
            "country": self.coordinator.council.country,
            "academic_year": status.academic_year,
            "current_term": status.current_term,
            "source_url": self.coordinator.council.source_url,
        }

