"""Config flow for UK School Terms."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_CLOSURE_DAYS,
    CONF_COUNCIL,
    CONF_COUNTRY,
    CONF_EXCLUDE_BANK_HOLIDAYS,
    CONF_INSET_DAYS,
    CONF_SCHOOL_NAME,
    DEFAULT_COUNTRY,
    DEFAULT_EXCLUDE_BANK_HOLIDAYS,
    DOMAIN,
)
from .data import list_councils
from .model import DateListError, parse_override_dates


def _multiline_selector() -> selector.TextSelector:
    return selector.TextSelector(
        selector.TextSelectorConfig(multiline=True, type=selector.TextSelectorType.TEXT)
    )


def _options_schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Optional(
                CONF_INSET_DAYS,
                default="\n".join(defaults.get(CONF_INSET_DAYS, [])),
            ): _multiline_selector(),
            vol.Optional(
                CONF_CLOSURE_DAYS,
                default="\n".join(defaults.get(CONF_CLOSURE_DAYS, [])),
            ): _multiline_selector(),
            vol.Required(
                CONF_EXCLUDE_BANK_HOLIDAYS,
                default=defaults.get(
                    CONF_EXCLUDE_BANK_HOLIDAYS, DEFAULT_EXCLUDE_BANK_HOLIDAYS
                ),
            ): bool,
        }
    )


def _validated_options(user_input: dict[str, Any]) -> dict[str, Any]:
    return {
        CONF_INSET_DAYS: parse_override_dates(user_input.get(CONF_INSET_DAYS)),
        CONF_CLOSURE_DAYS: parse_override_dates(user_input.get(CONF_CLOSURE_DAYS)),
        CONF_EXCLUDE_BANK_HOLIDAYS: user_input[CONF_EXCLUDE_BANK_HOLIDAYS],
    }


class UKSchoolTermsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for UK School Terms."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle initial setup."""
        errors: dict[str, str] = {}
        councils = await self.hass.async_add_executor_job(
            list_councils, DEFAULT_COUNTRY
        )

        if user_input is not None:
            try:
                overrides = _validated_options(user_input)
            except DateListError:
                errors["base"] = "invalid_date"
            else:
                council_id = user_input[CONF_COUNCIL]
                council_name = councils[council_id]
                school_name = user_input.get(CONF_SCHOOL_NAME, "").strip()
                suffix = f" - {school_name}" if school_name else ""
                title = self._unique_title(
                    f"UK School Terms - {council_name.replace(' County Council', '')}{suffix}"
                )
                data = {
                    CONF_COUNTRY: user_input[CONF_COUNTRY],
                    CONF_COUNCIL: council_id,
                    CONF_SCHOOL_NAME: school_name,
                    **overrides,
                }
                return self.async_create_entry(title=title, data=data)

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_COUNTRY, default=DEFAULT_COUNTRY
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            selector.SelectOptionDict(
                                value="england", label="England"
                            )
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(CONF_COUNCIL): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            selector.SelectOptionDict(value=value, label=label)
                            for value, label in councils.items()
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(CONF_SCHOOL_NAME, default=""): selector.TextSelector(),
                vol.Optional(CONF_INSET_DAYS, default=""): _multiline_selector(),
                vol.Optional(CONF_CLOSURE_DAYS, default=""): _multiline_selector(),
                vol.Required(
                    CONF_EXCLUDE_BANK_HOLIDAYS,
                    default=DEFAULT_EXCLUDE_BANK_HOLIDAYS,
                ): bool,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    def _unique_title(self, base_title: str) -> str:
        """Create a distinct title while deliberately allowing duplicate councils."""
        existing_titles = {entry.title for entry in self._async_current_entries()}
        if base_title not in existing_titles:
            return base_title
        index = 2
        while f"{base_title} {index}" in existing_titles:
            index += 1
        return f"{base_title} {index}"

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> UKSchoolTermsOptionsFlow:
        """Return the options flow."""
        return UKSchoolTermsOptionsFlow(config_entry)


class UKSchoolTermsOptionsFlow(config_entries.OptionsFlow):
    """Handle editable school-specific overrides."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options."""
        self._entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Manage options."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                options = _validated_options(user_input)
            except DateListError:
                errors["base"] = "invalid_date"
            else:
                return self.async_create_entry(title="", data=options)

        defaults = {
            key: self._entry.options.get(key, self._entry.data.get(key, default))
            for key, default in (
                (CONF_INSET_DAYS, []),
                (CONF_CLOSURE_DAYS, []),
                (CONF_EXCLUDE_BANK_HOLIDAYS, DEFAULT_EXCLUDE_BANK_HOLIDAYS),
            )
        }
        return self.async_show_form(
            step_id="init", data_schema=_options_schema(defaults), errors=errors
        )

