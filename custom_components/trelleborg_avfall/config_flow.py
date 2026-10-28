"""Konfigurationsflöde: anläggning och kärl läggs in av användaren."""

from __future__ import annotations

from datetime import date
from typing import Any
import uuid

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    DateSelector,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
)

from .const import (
    BIN_TYPES,
    CONF_ADDRESS,
    CONF_BIN_ID,
    CONF_BIN_NAME,
    CONF_BIN_TYPE,
    CONF_BINS,
    CONF_EXCLUDE_DATES,
    CONF_EXTRA_DATES,
    CONF_INTERVAL_WEEKS,
    CONF_REFERENCE_DATE,
    CONF_SEASON_END,
    CONF_SEASON_START,
    DOMAIN,
    PRESETS,
)
from .schedule import parse_date_list

BIN_TYPE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_BIN_TYPE): SelectSelector(
            SelectSelectorConfig(
                options=BIN_TYPES,
                translation_key=CONF_BIN_TYPE,
                mode=SelectSelectorMode.LIST,
            )
        )
    }
)

WEEK_SELECTOR = NumberSelector(
    NumberSelectorConfig(min=1, max=53, step=1, mode=NumberSelectorMode.BOX)
)


def _bin_schema(defaults: dict[str, Any]) -> vol.Schema:
    """Formulär för ett kärls schema, förifyllt med `defaults`."""

    def suggested(key: str) -> dict[str, Any]:
        value = defaults.get(key)
        return {"suggested_value": value} if value not in (None, "") else {}

    return vol.Schema(
        {
            vol.Required(CONF_BIN_NAME, description=suggested(CONF_BIN_NAME)): str,
            vol.Required(
                CONF_REFERENCE_DATE, description=suggested(CONF_REFERENCE_DATE)
            ): DateSelector(),
            vol.Required(
                CONF_INTERVAL_WEEKS, description=suggested(CONF_INTERVAL_WEEKS)
            ): NumberSelector(
                NumberSelectorConfig(
                    min=1,
                    max=52,
                    step=1,
                    mode=NumberSelectorMode.BOX,
                    unit_of_measurement="veckor",
                )
            ),
            vol.Optional(
                CONF_SEASON_START, description=suggested(CONF_SEASON_START)
            ): WEEK_SELECTOR,
            vol.Optional(
                CONF_SEASON_END, description=suggested(CONF_SEASON_END)
            ): WEEK_SELECTOR,
            vol.Optional(
                CONF_EXCLUDE_DATES, description=suggested(CONF_EXCLUDE_DATES)
            ): TextSelector(TextSelectorConfig(multiline=True)),
            vol.Optional(
                CONF_EXTRA_DATES, description=suggested(CONF_EXTRA_DATES)
            ): TextSelector(TextSelectorConfig(multiline=True)),
        }
    )


def _validate_bin(user_input: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str]]:
    """Validera och normalisera formulärdata. Returnerar (data, fel)."""
    errors: dict[str, str] = {}
    data = dict(user_input)
    data[CONF_BIN_NAME] = data[CONF_BIN_NAME].strip()
    data[CONF_INTERVAL_WEEKS] = int(data[CONF_INTERVAL_WEEKS])

    try:
        date.fromisoformat(data[CONF_REFERENCE_DATE])
    except (TypeError, ValueError):
        errors[CONF_REFERENCE_DATE] = "invalid_date"

    start, end = data.get(CONF_SEASON_START), data.get(CONF_SEASON_END)
    if (start is None) != (end is None):
        errors["base"] = "season_incomplete"
    for key in (CONF_SEASON_START, CONF_SEASON_END):
        if data.get(key) is not None:
            data[key] = int(data[key])
        else:
            data.pop(key, None)

    for key in (CONF_EXCLUDE_DATES, CONF_EXTRA_DATES):
        try:
            parse_date_list(data.get(key))
        except ValueError:
            errors[key] = "invalid_date_list"
        if not (data.get(key) or "").strip():
            data.pop(key, None)

    if not data[CONF_BIN_NAME]:
        errors[CONF_BIN_NAME] = "name_required"
    return data, errors


class TrelleborgAvfallConfigFlow(ConfigFlow, domain=DOMAIN):
    """Lägg till en anläggning med ett eller flera kärl."""

    VERSION = 1

    def __init__(self) -> None:
        self._address = ""
        self._bins: list[dict[str, Any]] = []
        self._bin_type = ""

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return TrelleborgAvfallOptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            self._address = user_input[CONF_ADDRESS].strip()
            if not self._address:
                errors[CONF_ADDRESS] = "name_required"
            else:
                await self.async_set_unique_id(self._address.lower())
                self._abort_if_unique_id_configured()
                return await self.async_step_bin_type()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_ADDRESS): str}),
            errors=errors,
        )

    async def async_step_bin_type(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            self._bin_type = user_input[CONF_BIN_TYPE]
            return await self.async_step_bin()
        return self.async_show_form(step_id="bin_type", data_schema=BIN_TYPE_SCHEMA)

    async def async_step_bin(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        defaults = dict(PRESETS[self._bin_type])
        if user_input is not None:
            data, errors = _validate_bin(user_input)
            if not errors:
                data[CONF_BIN_ID] = uuid.uuid4().hex
                data[CONF_BIN_TYPE] = self._bin_type
                self._bins.append(data)
                return await self.async_step_more()
            defaults = user_input

        return self.async_show_form(
            step_id="bin",
            data_schema=_bin_schema(defaults),
            errors=errors,
            description_placeholders={"count": str(len(self._bins) + 1)},
        )

    async def async_step_more(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return self.async_show_menu(
            step_id="more",
            menu_options=["bin_type", "finish"],
            description_placeholders={
                "bins": ", ".join(b[CONF_BIN_NAME] for b in self._bins)
            },
        )

    async def async_step_finish(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return self.async_create_entry(
            title=self._address,
            data={CONF_ADDRESS: self._address},
            options={CONF_BINS: self._bins},
        )


class TrelleborgAvfallOptionsFlow(OptionsFlow):
    """Lägg till, ändra eller ta bort kärl."""

    def __init__(self) -> None:
        self._bin_type = ""
        self._edit_id: str | None = None

    @property
    def _bins(self) -> list[dict[str, Any]]:
        return list(self.config_entry.options.get(CONF_BINS, []))

    def _bin_options(self) -> list[SelectOptionDict]:
        return [
            SelectOptionDict(value=b[CONF_BIN_ID], label=b[CONF_BIN_NAME])
            for b in self._bins
        ]

    def _save(self, bins: list[dict[str, Any]]) -> ConfigFlowResult:
        return self.async_create_entry(data={**self.config_entry.options, CONF_BINS: bins})

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        menu = ["add_bin"]
        if self._bins:
            menu += ["select_edit", "remove_bin"]
        return self.async_show_menu(step_id="init", menu_options=menu)

    async def async_step_add_bin(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            self._bin_type = user_input[CONF_BIN_TYPE]
            self._edit_id = None
            return await self.async_step_bin()
        return self.async_show_form(step_id="add_bin", data_schema=BIN_TYPE_SCHEMA)

    async def async_step_select_edit(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            self._edit_id = user_input[CONF_BIN_ID]
            return await self.async_step_bin()
        return self.async_show_form(
            step_id="select_edit",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_BIN_ID): SelectSelector(
                        SelectSelectorConfig(
                            options=self._bin_options(), mode=SelectSelectorMode.LIST
                        )
                    )
                }
            ),
        )

    async def async_step_bin(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        bins = self._bins
        existing = next((b for b in bins if b[CONF_BIN_ID] == self._edit_id), None)
        defaults = dict(existing) if existing else dict(PRESETS[self._bin_type])

        if user_input is not None:
            data, errors = _validate_bin(user_input)
            if not errors:
                if existing:
                    data[CONF_BIN_ID] = existing[CONF_BIN_ID]
                    data[CONF_BIN_TYPE] = existing.get(CONF_BIN_TYPE)
                    bins = [data if b is existing else b for b in bins]
                else:
                    data[CONF_BIN_ID] = uuid.uuid4().hex
                    data[CONF_BIN_TYPE] = self._bin_type
                    bins.append(data)
                return self._save(bins)
            defaults = user_input

        return self.async_show_form(
            step_id="bin", data_schema=_bin_schema(defaults), errors=errors
        )

    async def async_step_remove_bin(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            remove = set(user_input[CONF_BINS])
            return self._save([b for b in self._bins if b[CONF_BIN_ID] not in remove])
        return self.async_show_form(
            step_id="remove_bin",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_BINS): SelectSelector(
                        SelectSelectorConfig(
                            options=self._bin_options(),
                            multiple=True,
                            mode=SelectSelectorMode.LIST,
                        )
                    )
                }
            ),
        )
