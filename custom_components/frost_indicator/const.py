"""Constants for the Frost Indicator integration."""

from typing import Final

DOMAIN: Final = "frost_indicator"

# Config keys
CONF_WEATHER_ENTITY: Final = "weather_entity"
CONF_FROST_THRESHOLD: Final = "frost_threshold"

# Defaults
DEFAULT_FROST_THRESHOLD: Final = 0.0
DEFAULT_SCAN_INTERVAL_MINUTES: Final = 30
TONIGHT_CUTOFF_HOUR: Final = 9  # "Tonight" ends at 9am tomorrow

# Sensor states (priority order: highest to lowest)
STATE_FREEZING_NOW: Final = "freezing_now"
STATE_FROST_TONIGHT: Final = "frost_tonight"
STATE_FROST_SOON: Final = "frost_soon"
STATE_CLEAR: Final = "clear"

# Attributes
ATTR_CURRENT_TEMPERATURE: Final = "current_temperature"
ATTR_FORECAST_LOW: Final = "forecast_low_temperature"
ATTR_FIRST_FROST_DATE: Final = "first_frost_date"
ATTR_FROST_DAYS: Final = "frost_days_count"
ATTR_FROST_THRESHOLD: Final = "frost_threshold"
ATTR_WEATHER_ENTITY: Final = "weather_entity"
ATTR_FORECAST_HOURS: Final = "forecast_hours_available"
ATTR_FORECAST_DAYS: Final = "forecast_days_available"
