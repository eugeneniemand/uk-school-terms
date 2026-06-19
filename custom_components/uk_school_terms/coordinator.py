"""Coordinator for UK School Terms."""

from __future__ import annotations

from datetime import datetime, time, timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.event import async_track_point_in_time
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .bank_holidays import get_bank_holidays
from .const import (
    CONF_CLOSURE_DAYS,
    CONF_EXCLUDE_BANK_HOLIDAYS,
    CONF_INSET_DAYS,
    DEFAULT_EXCLUDE_BANK_HOLIDAYS,
    DOMAIN,
)
from .model import CouncilData, SchoolDayStatus, SchoolEvent, calculate_status, next_event

_LOGGER = logging.getLogger(__name__)


class UKSchoolTermsCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Calculate local school-term state once each day."""

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, council: CouncilData
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
        )
        self.entry = entry
        self.council = council
        self._cancel_midnight_update: CALLBACK_TYPE | None = None

    def _setting(self, key: str, default: Any) -> Any:
        """Return an option, falling back to initial entry data."""
        return self.entry.options.get(key, self.entry.data.get(key, default))

    async def _async_update_data(self) -> dict[str, Any]:
        """Calculate state using Home Assistant's local date."""
        today = dt_util.now().date()
        status: SchoolDayStatus = calculate_status(
            self.council,
            today,
            inset_days=self._setting(CONF_INSET_DAYS, []),
            closure_days=self._setting(CONF_CLOSURE_DAYS, []),
            exclude_bank_holidays=self._setting(
                CONF_EXCLUDE_BANK_HOLIDAYS, DEFAULT_EXCLUDE_BANK_HOLIDAYS
            ),
            bank_holidays=get_bank_holidays(self.council.country, today.year),
        )
        event: SchoolEvent | None = next_event(self.council, today)
        return {"date": today, "status": status, "next_event": event}

    @callback
    def async_schedule_midnight_update(self) -> None:
        """Schedule a refresh shortly after the next local midnight."""
        if self._cancel_midnight_update is not None:
            self._cancel_midnight_update()

        now = dt_util.now()
        tomorrow = now.date() + timedelta(days=1)
        next_update_local = datetime.combine(
            tomorrow, time(hour=0, minute=5), tzinfo=dt_util.DEFAULT_TIME_ZONE
        )
        self._cancel_midnight_update = async_track_point_in_time(
            self.hass, self._async_midnight_update, dt_util.as_utc(next_update_local)
        )

    async def _async_midnight_update(self, _now: datetime) -> None:
        """Refresh and schedule the following daily update."""
        await self.async_request_refresh()
        self.async_schedule_midnight_update()

    @callback
    def async_shutdown_daily_update(self) -> None:
        """Cancel the scheduled daily refresh."""
        if self._cancel_midnight_update is not None:
            self._cancel_midnight_update()
            self._cancel_midnight_update = None

