"""Calendar for UK School Terms."""

from __future__ import annotations

from datetime import datetime, timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DATA_COORDINATOR, DOMAIN
from .coordinator import UKSchoolTermsCoordinator
from .entity import UKSchoolTermsEntity
from .model import Term, current_term, future_terms


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the school terms calendar."""
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    async_add_entities([UKSchoolTermsCalendar(coordinator)])


class UKSchoolTermsCalendar(UKSchoolTermsEntity, CalendarEntity):
    """Calendar containing term and half-term ranges."""

    _attr_translation_key = "school_terms"

    def __init__(self, coordinator: UKSchoolTermsCoordinator) -> None:
        super().__init__(coordinator, "school_terms")

    def _events(self) -> list[CalendarEvent]:
        events: list[CalendarEvent] = []
        for term in self.coordinator.council.terms:
            events.append(
                CalendarEvent(
                    summary=f"{term.name} term",
                    start=term.dates.start,
                    end=term.dates.end + timedelta(days=1),
                    description=(
                        f"{self.coordinator.council.name} ({term.academic_year})"
                    ),
                )
            )
            for half_term in term.half_terms:
                events.append(
                    CalendarEvent(
                        summary=f"{term.name} half-term",
                        start=half_term.start,
                        end=half_term.end + timedelta(days=1),
                        description=(
                            f"{self.coordinator.council.name} "
                            f"({term.academic_year})"
                        ),
                    )
                )
        return sorted(events, key=lambda event: event.start)

    @staticmethod
    def _term_attributes(term: Term) -> dict[str, object]:
        """Represent a term as Home Assistant state attributes."""
        return {
            "name": term.name,
            "academic_year": term.academic_year,
            "start": term.dates.start.isoformat(),
            "end": term.dates.end.isoformat(),
            "half_terms": [
                {
                    "start": half_term.start.isoformat(),
                    "end": half_term.end.isoformat(),
                }
                for half_term in term.half_terms
            ],
        }

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        """Expose the current term and all future defined terms."""
        today = self.coordinator.data["date"]
        active_term = current_term(self.coordinator.council, today)
        return {
            "current_term": (
                self._term_attributes(active_term) if active_term else None
            ),
            "future_terms": [
                self._term_attributes(term)
                for term in future_terms(self.coordinator.council, today)
            ],
        }

    @property
    def event(self) -> CalendarEvent | None:
        today = self.coordinator.data["date"]
        active = [
            event
            for event in self._events()
            if event.start <= today < event.end
        ]
        if not active:
            return None
        return min(active, key=lambda item: (item.end - item.start).days)

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        """Return events overlapping a requested interval."""
        start = start_date.date()
        end = end_date.date()
        return [
            event
            for event in self._events()
            if event.start < end and event.end > start
        ]

