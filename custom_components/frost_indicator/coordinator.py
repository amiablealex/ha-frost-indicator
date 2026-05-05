"""Data update coordinator for the Frost Indicator integration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DOMAIN,
    STATE_CLEAR,
    STATE_FREEZING_NOW,
    STATE_FROST_SOON,
    STATE_FROST_TONIGHT,
    TONIGHT_CUTOFF_HOUR,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class FrostData:
    """Processed frost indicator data."""

    state: str
    current_temperature: float | None
    forecast_low: float | None
    first_frost_date: str | None
    frost_days_count: int
    forecast_hours_available: int
    forecast_days_available: int


class FrostIndicatorCoordinator(DataUpdateCoordinator[FrostData]):
    """Coordinator to fetch weather forecasts and determine frost risk."""

    def __init__(
        self,
        hass: HomeAssistant,
        weather_entity: str,
        frost_threshold: float,
    ) -> None:
        """Initialise the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=DEFAULT_SCAN_INTERVAL_MINUTES),
        )
        self.weather_entity = weather_entity
        self.frost_threshold = frost_threshold

    async def _async_update_data(self) -> FrostData:
        """Fetch forecast data and analyse for frost risk."""
        current_temp = self._get_current_temperature()
        hourly = await self._fetch_forecast("hourly")
        daily = await self._fetch_forecast("daily")

        if hourly is None and daily is None:
            raise UpdateFailed(
                f"Could not fetch any forecast data from {self.weather_entity}"
            )

        now = datetime.now().astimezone()
        tonight_cutoff = self._get_tonight_cutoff(now)

        tonight_entries = self._filter_entries(hourly or [], now, tonight_cutoff)
        future_entries = self._filter_entries(daily or [], tonight_cutoff, None)

        # If hourly wasn't available, use daily for tonight too
        if hourly is None and daily is not None:
            tonight_entries = self._filter_entries(daily, now, tonight_cutoff)

        return self._analyse(
            current_temp=current_temp,
            tonight_entries=tonight_entries,
            future_entries=future_entries,
            hourly_count=len(hourly) if hourly else 0,
            daily_count=len(daily) if daily else 0,
        )

    def _get_current_temperature(self) -> float | None:
        """Get the current temperature from the weather entity."""
        state = self.hass.states.get(self.weather_entity)
        if state is None:
            return None
        temp = state.attributes.get("temperature")
        if temp is None:
            return None
        try:
            return float(temp)
        except (ValueError, TypeError):
            return None

    async def _fetch_forecast(self, forecast_type: str) -> list[dict] | None:
        """Fetch forecast data, returning None if unavailable."""
        try:
            response = await self.hass.services.async_call(
                "weather",
                "get_forecasts",
                {
                    "type": forecast_type,
                    "entity_id": self.weather_entity,
                },
                blocking=True,
                return_response=True,
            )
        except HomeAssistantError:
            _LOGGER.debug(
                "Could not fetch %s forecast from %s",
                forecast_type,
                self.weather_entity,
            )
            return None

        if response is None or self.weather_entity not in response:
            return None

        forecasts = response[self.weather_entity].get("forecast", [])
        return forecasts if forecasts else None

    @staticmethod
    def _get_tonight_cutoff(now: datetime) -> datetime:
        """Calculate the 'tonight' cutoff: 9am tomorrow."""
        tomorrow = now + timedelta(days=1)
        return tomorrow.replace(
            hour=TONIGHT_CUTOFF_HOUR, minute=0, second=0, microsecond=0
        )

    @staticmethod
    def _filter_entries(
        entries: list[dict],
        after: datetime,
        before: datetime | None,
    ) -> list[dict]:
        """Filter forecast entries to a time window."""
        filtered = []
        for entry in entries:
            dt_str = entry.get("datetime")
            if not dt_str:
                continue
            try:
                dt = datetime.fromisoformat(dt_str)
            except (ValueError, TypeError):
                continue
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=after.tzinfo)
            if dt < after:
                continue
            if before is not None and dt >= before:
                continue
            filtered.append(entry)
        return filtered

    def _analyse(
        self,
        current_temp: float | None,
        tonight_entries: list[dict],
        future_entries: list[dict],
        hourly_count: int,
        daily_count: int,
    ) -> FrostData:
        """Determine frost state from current temp and forecast entries."""
        is_freezing_now = (
            current_temp is not None and current_temp <= self.frost_threshold
        )

        tonight_frost, tonight_low, tonight_frost_date = self._scan_entries(
            tonight_entries
        )
        future_frost, future_low, future_frost_date = self._scan_entries(future_entries)

        # Overall lowest temperature across all data
        lows = [t for t in [current_temp, tonight_low, future_low] if t is not None]
        forecast_low = min(lows) if lows else None

        # First frost date (tonight takes priority)
        first_frost_date = tonight_frost_date or future_frost_date

        # Count frost days in future entries
        frost_days = sum(
            1
            for e in future_entries
            if self._get_effective_temp(e) is not None
            and self._get_effective_temp(e) <= self.frost_threshold
        )

        # State in priority order
        if is_freezing_now:
            state = STATE_FREEZING_NOW
        elif tonight_frost:
            state = STATE_FROST_TONIGHT
        elif future_frost:
            state = STATE_FROST_SOON
        else:
            state = STATE_CLEAR

        return FrostData(
            state=state,
            current_temperature=current_temp,
            forecast_low=forecast_low,
            first_frost_date=first_frost_date,
            frost_days_count=frost_days,
            forecast_hours_available=hourly_count,
            forecast_days_available=daily_count,
        )

    def _scan_entries(
        self, entries: list[dict]
    ) -> tuple[bool, float | None, str | None]:
        """Scan entries for frost. Returns (has_frost, lowest_temp, first_frost_date)."""
        lowest: float | None = None
        first_frost_date: str | None = None
        has_frost = False

        for entry in entries:
            temp = self._get_effective_temp(entry)
            if temp is None:
                continue
            if lowest is None or temp < lowest:
                lowest = temp
            if temp <= self.frost_threshold:
                has_frost = True
                if first_frost_date is None:
                    first_frost_date = entry.get("datetime")

        return has_frost, lowest, first_frost_date

    @staticmethod
    def _get_effective_temp(entry: dict) -> float | None:
        """Get the relevant temperature from a forecast entry.

        Daily forecasts provide 'templow' for the overnight minimum.
        Hourly forecasts just provide 'temperature'.
        """
        temp_low = entry.get("templow")
        temp = entry.get("temperature")
        value = temp_low if temp_low is not None else temp
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
