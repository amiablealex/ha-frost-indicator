"""Sensor platform for the Frost Indicator integration."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_CURRENT_TEMPERATURE,
    ATTR_FIRST_FROST_DATE,
    ATTR_FORECAST_DAYS,
    ATTR_FORECAST_HOURS,
    ATTR_FORECAST_LOW,
    ATTR_FROST_DAYS,
    ATTR_FROST_THRESHOLD,
    ATTR_WEATHER_ENTITY,
    CONF_FROST_THRESHOLD,
    CONF_WEATHER_ENTITY,
    DEFAULT_FROST_THRESHOLD,
    DOMAIN,
    STATE_CLEAR,
    STATE_FREEZING_NOW,
    STATE_FROST_SOON,
    STATE_FROST_TONIGHT,
)
from .coordinator import FrostData, FrostIndicatorCoordinator

STATE_ICONS: dict[str, str] = {
    STATE_FREEZING_NOW: "mdi:snowflake-alert",
    STATE_FROST_TONIGHT: "mdi:snowflake",
    STATE_FROST_SOON: "mdi:snowflake-melt",
    STATE_CLEAR: "mdi:weather-sunny",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Frost Indicator sensor from a config entry."""
    coordinator: FrostIndicatorCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([FrostIndicatorSensor(coordinator, entry)])


class FrostIndicatorSensor(CoordinatorEntity[FrostIndicatorCoordinator], SensorEntity):
    """Sensor that indicates the frost risk level."""

    _attr_has_entity_name = True
    _attr_translation_key = "frost_indicator"

    def __init__(
        self,
        coordinator: FrostIndicatorCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialise the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_frost_indicator"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            entry_type=DeviceEntryType.SERVICE,
            manufacturer="Gardener's Frost Indicator",
        )

    @property
    def native_value(self) -> str | None:
        """Return the current frost risk state."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.state

    @property
    def icon(self) -> str:
        """Return an icon based on the frost risk level."""
        if self.coordinator.data is None:
            return "mdi:snowflake-alert"
        return STATE_ICONS.get(self.coordinator.data.state, "mdi:snowflake-alert")

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional state attributes."""
        data: FrostData | None = self.coordinator.data
        threshold = self._entry.options.get(
            CONF_FROST_THRESHOLD,
            self._entry.data.get(CONF_FROST_THRESHOLD, DEFAULT_FROST_THRESHOLD),
        )
        weather_entity = self._entry.data.get(CONF_WEATHER_ENTITY)

        attrs: dict = {
            ATTR_FROST_THRESHOLD: threshold,
            ATTR_WEATHER_ENTITY: weather_entity,
        }

        if data is not None:
            attrs.update(
                {
                    ATTR_CURRENT_TEMPERATURE: data.current_temperature,
                    ATTR_FORECAST_LOW: data.forecast_low,
                    ATTR_FIRST_FROST_DATE: data.first_frost_date,
                    ATTR_FROST_DAYS: data.frost_days_count,
                    ATTR_FORECAST_HOURS: data.forecast_hours_available,
                    ATTR_FORECAST_DAYS: data.forecast_days_available,
                }
            )

        return attrs
