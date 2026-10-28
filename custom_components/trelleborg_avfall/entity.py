"""Gemensam basklass för entiteter."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_track_time_change

from .const import CONF_BINS, DOMAIN
from .schedule import BinSchedule


def load_bins(entry: ConfigEntry) -> list[tuple[dict[str, Any], BinSchedule]]:
    """Läs kärlen och deras scheman från konfigurationen."""
    return [
        (bin_cfg, BinSchedule.from_config(bin_cfg))
        for bin_cfg in entry.options.get(CONF_BINS, [])
    ]


class TrelleborgEntity(Entity):
    """Bas för entiteter som räknas om vid midnatt."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, entry: ConfigEntry) -> None:
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Trelleborg Kretslopp och Vatten",
            model="Avfallsabonnemang",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url="https://www.trelleborg.se/",
        )

    async def async_added_to_hass(self) -> None:
        """Uppdatera när datumet byts."""
        self.async_on_remove(
            async_track_time_change(
                self.hass, self._async_new_day, hour=0, minute=0, second=5
            )
        )

    @callback
    def _async_new_day(self, _now: datetime) -> None:
        self.async_write_ha_state()
