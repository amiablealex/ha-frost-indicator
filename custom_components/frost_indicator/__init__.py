"""The Frost Indicator integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import (
    CONF_FROST_THRESHOLD,
    CONF_WEATHER_ENTITY,
    DEFAULT_FROST_THRESHOLD,
    DOMAIN,
)
from .coordinator import FrostIndicatorCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Frost Indicator from a config entry."""
    weather_entity = entry.data[CONF_WEATHER_ENTITY]

    # Threshold can come from options (if changed) or initial data
    frost_threshold = entry.options.get(
        CONF_FROST_THRESHOLD,
        entry.data.get(CONF_FROST_THRESHOLD, DEFAULT_FROST_THRESHOLD),
    )

    coordinator = FrostIndicatorCoordinator(
        hass,
        weather_entity=weather_entity,
        frost_threshold=frost_threshold,
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update — reload the integration."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
