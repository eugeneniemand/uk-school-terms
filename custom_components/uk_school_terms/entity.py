"""Shared entity base for UK School Terms."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import UKSchoolTermsCoordinator


class UKSchoolTermsEntity(CoordinatorEntity[UKSchoolTermsCoordinator]):
    """Base entity for a UK School Terms entry."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: UKSchoolTermsCoordinator, entity_key: str
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{entity_key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.entry.entry_id)},
            name=coordinator.entry.title,
            manufacturer="UK School Terms",
            model="Static council term dates",
            configuration_url=coordinator.council.source_url,
        )

