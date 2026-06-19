"""The UK School Terms integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_COUNCIL, CONF_COUNTRY, DATA_COORDINATOR, DOMAIN, PLATFORMS
from .coordinator import UKSchoolTermsCoordinator
from .data import load_council


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up UK School Terms from a config entry."""
    council = await hass.async_add_executor_job(
        load_council, entry.data[CONF_COUNTRY], entry.data[CONF_COUNCIL]
    )
    coordinator = UKSchoolTermsCoordinator(hass, entry, council)
    await coordinator.async_config_entry_first_refresh()
    coordinator.async_schedule_midnight_update()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        DATA_COORDINATOR: coordinator
    }
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        coordinator: UKSchoolTermsCoordinator = hass.data[DOMAIN][entry.entry_id][
            DATA_COORDINATOR
        ]
        coordinator.async_shutdown_daily_update()
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def _async_update_listener(
    hass: HomeAssistant, entry: ConfigEntry
) -> None:
    """Reload an entry after its options change."""
    await hass.config_entries.async_reload(entry.entry_id)

