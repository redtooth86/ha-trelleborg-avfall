"""Kalender med alla tömningsdagar."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import CONF_BIN_NAME, CONF_BIN_TYPE, CONTENTS
from .entity import TrelleborgEntity, load_bins
from .schedule import SEARCH_HORIZON, BinSchedule


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Skapa tömningskalendern."""
    bins = load_bins(entry)
    if bins:
        async_add_entities([CollectionCalendar(entry, bins)])


class CollectionCalendar(TrelleborgEntity, CalendarEntity):
    """Alla kärls tömningar som heldagshändelser."""

    _attr_translation_key = "collections"
    _attr_icon = "mdi:calendar-blank"

    def __init__(
        self, entry: ConfigEntry, bins: list[tuple[dict[str, Any], BinSchedule]]
    ) -> None:
        super().__init__(entry)
        self._bins = bins
        self._attr_unique_id = f"{entry.entry_id}_calendar"

    def _events(self, start: date, end: date) -> list[CalendarEvent]:
        events = [
            CalendarEvent(
                start=day,
                end=day + timedelta(days=1),
                summary=cfg[CONF_BIN_NAME],
                description=CONTENTS.get(cfg.get(CONF_BIN_TYPE), "") or None,
            )
            for cfg, schedule in self._bins
            for day in schedule.occurrences(start, end)
        ]
        return sorted(events, key=lambda e: (e.start, e.summary))

    @property
    def event(self) -> CalendarEvent | None:
        today = dt_util.now().date()
        # Sök i växande fönster så att vi inte räknar hela horisonten i onödan.
        for days in (31, 186, SEARCH_HORIZON.days):
            events = self._events(today, today + timedelta(days=days))
            if events:
                return events[0]
        return None

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        start = dt_util.as_local(start_date).date()
        # end_date är exklusivt: slutar intervallet vid midnatt ingår inte den dagen.
        end_local = dt_util.as_local(end_date)
        end = end_local.date()
        if end_local.time() == datetime.min.time() and end > start:
            end -= timedelta(days=1)
        return self._events(start, end)
