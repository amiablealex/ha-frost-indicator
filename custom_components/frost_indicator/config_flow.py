"""Config flow for the Frost Indicator integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_FROST_THRESHOLD,
    CONF_WEATHER_ENTITY,
    DEFAULT_FROST_THRESHOLD,
    DOMAIN,
)


class FrostIndicatorConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Frost Indicator."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> FrostIndicatorOptionsFlow:
        """Get the options flow handler."""
        return FrostIndicatorOptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        # Check if any weather entities exist
        weather_states = self.hass.states.async_entity_ids("weather")
        if not weather_states:
            return self.async_abort(reason="no_weather")

        errors: dict[str, str] = {}

        if user_input is not None:
            weather_entity = user_input[CONF_WEATHER_ENTITY]

            state = self.hass.states.get(weather_entity)
            if state is None:
                errors["base"] = "weather_not_found"
            else:
                await self.async_set_unique_id(weather_entity)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"Frost ({state.name})",
                    data=user_input,
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_WEATHER_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="weather"),
                ),
                vol.Optional(
                    CONF_FROST_THRESHOLD,
                    default=DEFAULT_FROST_THRESHOLD,
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=-10.0,
                        max=10.0,
                        step=0.5,
                        mode=selector.NumberSelectorMode.BOX,
                    ),
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )


class FrostIndicatorOptionsFlow(OptionsFlow):
    """Handle options for Frost Indicator."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle options flow."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        current_threshold = self.config_entry.options.get(
            CONF_FROST_THRESHOLD,
            self.config_entry.data.get(CONF_FROST_THRESHOLD, DEFAULT_FROST_THRESHOLD),
        )

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_FROST_THRESHOLD,
                    default=current_threshold,
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=-10.0,
                        max=10.0,
                        step=0.5,
                        mode=selector.NumberSelectorMode.BOX,
                    ),
                ),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
