"""Kör hela flödet i Home Assistant: lägg till anläggning, kärl, ändra och ta bort.

Kör: pip install pytest-homeassistant-custom-component && pytest tests/ha
"""

from datetime import date, timedelta

from freezegun.api import FrozenDateTimeFactory
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er

from custom_components.trelleborg_avfall.const import CONF_BINS, DOMAIN


async def _add_bin(hass, flow_id, bin_type, **fields):
    result = await hass.config_entries.flow.async_configure(flow_id, {"bin_type": bin_type})
    assert result["step_id"] == "bin"
    return await hass.config_entries.flow.async_configure(flow_id, fields)


async def test_full_flow(hass: HomeAssistant, freezer: FrozenDateTimeFactory) -> None:
    freezer.move_to("2026-10-28 12:00:00+01:00")
    await hass.config.async_set_time_zone("Europe/Stockholm")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"address": "Östergatan 42 ANDERSLÖV"}
    )
    assert result["step_id"] == "bin_type"
    flow_id = result["flow_id"]

    result = await _add_bin(
        hass, flow_id, "fyrfack_1",
        name="Kärl 1", reference_date="2026-11-04", interval_weeks=2,
    )
    assert result["type"] is FlowResultType.MENU
    result = await hass.config_entries.flow.async_configure(flow_id, {"next_step_id": "bin_type"})
    result = await _add_bin(
        hass, flow_id, "fyrfack_2",
        name="Kärl 2", reference_date="2026-11-19", interval_weeks=4,
    )
    result = await hass.config_entries.flow.async_configure(flow_id, {"next_step_id": "bin_type"})
    # Ofullständig säsong ger fel
    result = await _add_bin(
        hass, flow_id, "garden",
        name="Trädgård", reference_date="2026-11-09", interval_weeks=2, season_start_week=12,
    )
    assert result["errors"] == {"base": "season_incomplete"}
    result = await hass.config_entries.flow.async_configure(
        flow_id,
        {"name": "Trädgård", "reference_date": "2026-11-09", "interval_weeks": 2,
         "season_start_week": 12, "season_end_week": 47},
    )
    result = await hass.config_entries.flow.async_configure(flow_id, {"next_step_id": "finish"})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()

    entry = hass.config_entries.async_entries(DOMAIN)[0]
    registry = er.async_get(hass)
    ids = {e.unique_id: e.entity_id for e in er.async_entries_for_config_entry(registry, entry.entry_id)}
    assert len(ids) == 5  # 3 kärl + nästa tömning + kalender

    bins = entry.options[CONF_BINS]
    state = {b["name"]: hass.states.get(ids[f"{entry.entry_id}_{b['id']}"]) for b in bins}
    k1 = state["Kärl 1"]
    assert k1.state == "2026-11-04"
    assert k1.attributes["days_until"] == 7
    assert k1.attributes["friendly_name"] == "Östergatan 42 ANDERSLÖV Kärl 1"
    assert state["Kärl 2"].state == "2026-11-19"
    garden = state["Trädgård"]
    # Enligt hämtschemat: sista för säsongen 9 nov, sedan 14-dagarsrytm från v.13
    assert garden.state == "2026-11-09"
    assert garden.attributes["upcoming"][:2] == ["2026-11-09", "2027-03-29"]

    nxt = hass.states.get(ids[f"{entry.entry_id}_next"])
    assert nxt.state == "2026-11-04"
    assert nxt.attributes["bins"] == ["Kärl 1"]

    cal_id = ids[f"{entry.entry_id}_calendar"]
    events = await hass.services.async_call(
        "calendar", "get_events",
        {"entity_id": cal_id, "start_date_time": "2026-11-01 00:00:00", "end_date_time": "2026-12-01 00:00:00"},
        blocking=True, return_response=True,
    )
    days = [(e["start"], e["summary"]) for e in events[cal_id]["events"]]
    assert days == [
        ("2026-11-04", "Kärl 1"), ("2026-11-09", "Trädgård"), ("2026-11-18", "Kärl 1"), ("2026-11-19", "Kärl 2"),
    ]

    # Byt dag: sensorn räknas om vid midnatt
    freezer.move_to("2026-11-05 00:00:06+01:00")
    from pytest_homeassistant_custom_component.common import async_fire_time_changed
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert hass.states.get(k1.entity_id).state == "2026-11-18"

    # Options: ändra kärl 1 och ta bort kärl 2
    k1_id = bins[0]["id"]
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.MENU
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"next_step_id": "select_edit"})
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"id": k1_id})
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"name": "Kärl 1", "reference_date": "2026-11-06", "interval_weeks": 1}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert hass.states.get(k1.entity_id).state == "2026-11-06"

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"next_step_id": "remove_bin"})
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"bins": [bins[1]["id"]]})
    await hass.async_block_till_done()
    remaining = er.async_entries_for_config_entry(registry, entry.entry_id)
    assert len(remaining) == 4
    assert ids[f"{entry.entry_id}_{bins[1]['id']}"] not in {e.entity_id for e in remaining}


async def test_duplicate_address(hass: HomeAssistant) -> None:
    for expected in (FlowResultType.FORM, FlowResultType.ABORT):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {"address": "Testgatan 1"})
        if expected is FlowResultType.FORM:
            result = await _add_bin(hass, result["flow_id"], "other", name="X", reference_date="2026-01-01", interval_weeks=1)
            await hass.config_entries.flow.async_configure(result["flow_id"], {"next_step_id": "finish"})
        else:
            assert result["type"] is FlowResultType.ABORT
