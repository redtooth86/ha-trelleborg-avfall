"""Trelleborg Kretslopp och Vatten – tömningsschema för avfallskärl."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import CONF_BIN_ID, CONF_BINS

PLATFORMS = [Platform.SENSOR, Platform.CALENDAR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Sätt upp en anläggning."""
    _remove_stale_entities(hass, entry)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Ta bort en anläggning."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Ladda om när kärl läggs till, ändras eller tas bort."""
    await hass.config_entries.async_reload(entry.entry_id)


def _remove_stale_entities(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Ta bort entiteter för kärl som inte längre finns."""
    expected = {f"{entry.entry_id}_next", f"{entry.entry_id}_calendar"}
    expected.update(
        f"{entry.entry_id}_{bin_cfg[CONF_BIN_ID]}"
        for bin_cfg in entry.options.get(CONF_BINS, [])
    )
    registry = er.async_get(hass)
    for reg_entry in er.async_entries_for_config_entry(registry, entry.entry_id):
        if reg_entry.unique_id not in expected:
            registry.async_remove(reg_entry.entity_id)
