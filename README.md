# Gardener's Frost Indicator for Home Assistant

A Home Assistant integration that tells you if your plants are about to have a bad night.

It reads forecast data from whatever weather integration you already have running and distils it down to one of four states: **Freezing now**, **Frost tonight**, **Frost soon**, or **Clear**. That's it. No dashboards, no graphs, no opinions on your mulching technique.

## How it works

The integration calls your weather entity's forecast service every 30 minutes. It checks hourly forecasts for the overnight window (now until 9am tomorrow) and daily forecasts for the longer outlook. If any forecast temperature falls at or below your configured threshold, the sensor updates accordingly.

It does not call any external APIs. It does not need API keys. It reads data your weather integration already provides and tells you whether to worry.

**An important caveat:** this integration is only as good as the weather data behind it. If your weather provider only returns 2 days of forecast data, the "frost soon" state can only see 2 days ahead. If you want a 5-day outlook, you need a weather integration that provides 5 days of forecasts. Garbage in, frost out.

## States

| State | What it means | What to do |
|---|---|---|
| Freezing now | Current temperature is at or below threshold | It is already too late for prevention. Consider a hot drink. |
| Frost tonight | Frost forecast between now and 9am tomorrow | Cover tender plants, move pots inside, drain exposed pipes |
| Frost soon | Frost forecast within the available forecast period | Keep an eye on it. Make plans. |
| Clear | No frost in the forecast | Carry on gardening |

## Sensor attributes

The sensor exposes forecast details as attributes for use in automations and templates: `current_temperature`, `forecast_low_temperature`, `first_frost_date`, `frost_days_count`, `frost_threshold`, `forecast_hours_available`, `forecast_days_available`, and `last_updated`.

## Installation

### HACS (recommended)

1. Open HACS in Home Assistant
2. Three-dot menu, Custom repositories
3. Add `https://github.com/amiablealex/ha-frost-indicator` as an Integration
4. Search for "Frost Indicator" and install
5. Restart Home Assistant

### Manual

Copy the `custom_components/frost_indicator` folder into your Home Assistant `config/custom_components/` directory. Restart Home Assistant.

## Setup

Settings, Devices & Services, Add Integration, search "Frost Indicator". Pick your weather entity, set your frost threshold (default 0°C — raise it to 2°C if you grow anything that bruises easily), and you're done.

The threshold can be changed later without reinstalling — go to the integration's options.

## Requirements

- Home Assistant 2024.7.0 or newer
- At least one weather integration (Met Office, OpenWeatherMap, Met.no, or anything that supports `weather.get_forecasts`)

If you have no weather integration, the setup wizard will politely decline to proceed and suggest you install one first.

## Example automations

### The concerned gardener

```yaml
automation:
  - alias: "Frost tonight — protect the vegetable patch"
    trigger:
      - platform: state
        entity_id: sensor.frost_indicator
        to: "frost_tonight"
    action:
      - service: notify.notify
        data:
          title: "Frost tonight"
          message: >-
            Forecast low is
            {{ state_attr('sensor.frost_indicator', 'forecast_low_temperature') }}°C.
            Your courgettes would like a blanket.
```

### The forward planner

```yaml
automation:
  - alias: "Frost coming this week"
    trigger:
      - platform: state
        entity_id: sensor.frost_indicator
        to: "frost_soon"
    action:
      - service: notify.notify
        data:
          title: "Frost on the horizon"
          message: >-
            First frost expected
            {{ state_attr('sensor.frost_indicator', 'first_frost_date') }}.
            {{ state_attr('sensor.frost_indicator', 'frost_days_count') }} frost days
            in the forecast.
```

## Contributing

Issues and pull requests welcome. If you find a bug, please include your weather integration name and HA version — it helps narrow things down.

## Licence

MIT. See [LICENCE](LICENCE) for details.
