"""Sensorer med nästa tömningsdag."""

from __future__ import annotations

from datetime import date
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import (
    CONF_BIN_ID,
    CONF_BIN_NAME,
    CONF_BIN_TYPE,
    CONF_INTERVAL_WEEKS,
    CONF_SEASON_END,
    CONF_SEASON_START,
    CONTENTS,
    ICONS,
    UPCOMING_COUNT,
)
from .entity import TrelleborgEntity, load_bins
from .schedule import BinSchedule


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Skapa en sensor per kärl plus en sammanfattande sensor."""
    bins = load_bins(entry)
    entities: list[SensorEntity] = [
        BinSensor(entry, bin_cfg, schedule) for bin_cfg, schedule in bins
    ]
    if bins:
        entities.append(NextCollectionSensor(entry, bins))
    async_add_entities(entities)


def _days_until(day: date | None) -> int | None:
    return (day - dt_util.now().date()).days if day else None


class BinSensor(TrelleborgEntity, SensorEntity):
    """Nästa tömning för ett kärl."""

    _attr_device_class = SensorDeviceClass.DATE

    def __init__(
        self, entry: ConfigEntry, bin_cfg: dict[str, Any], schedule: BinSchedule
    ) -> None:
        super().__init__(entry)
        self._cfg = bin_cfg
        self._schedule = schedule
        self._attr_name = bin_cfg[CONF_BIN_NAME]
        self._attr_unique_id = f"{entry.entry_id}_{bin_cfg[CONF_BIN_ID]}"
        self._attr_icon = ICONS.get(bin_cfg.get(CONF_BIN_TYPE), "mdi:delete-variant")

    @property
    def native_value(self) -> date | None:
        return self._schedule.next_collection(dt_util.now().date())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        upcoming = self._schedule.upcoming(dt_util.now().date(), UPCOMING_COUNT)
        attrs: dict[str, Any] = {
            "days_until": _days_until(upcoming[0] if upcoming else None),
            "upcoming": [d.isoformat() for d in upcoming],
            "interval_weeks": int(self._cfg[CONF_INTERVAL_WEEKS]),
            "contents": CONTENTS.get(self._cfg.get(CONF_BIN_TYPE), ""),
        }
        if self._cfg.get(CONF_SEASON_START) and self._cfg.get(CONF_SEASON_END):
            attrs["season"] = (
                f"v.{int(self._cfg[CONF_SEASON_START])}-{int(self._cfg[CONF_SEASON_END])}"
            )
        return attrs


class NextCollectionSensor(TrelleborgEntity, SensorEntity):
    """Nästa tömning av något kärl på anläggningen."""

    _attr_device_class = SensorDeviceClass.DATE
    _attr_translation_key = "next_collection"
    _attr_icon = "mdi:truck"

    def __init__(
        self, entry: ConfigEntry, bins: list[tuple[dict[str, Any], BinSchedule]]
    ) -> None:
        super().__init__(entry)
        self._bins = bins
        self._attr_unique_id = f"{entry.entry_id}_next"

    def _next(self) -> tuple[date | None, list[str]]:
        today = dt_util.now().date()
        dates = [(s.next_collection(today), cfg[CONF_BIN_NAME]) for cfg, s in self._bins]
        dates = [(d, name) for d, name in dates if d]
        if not dates:
            return None, []
        first = min(d for d, _ in dates)
        return first, [name for d, name in dates if d == first]

    @property
    def native_value(self) -> date | None:
        return self._next()[0]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        day, names = self._next()
        return {"days_until": _days_until(day), "bins": names}
