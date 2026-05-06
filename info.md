A Home Assistant integration that tells you if your plants are about to have a bad night.

Point it at any weather entity you already have running. It checks the forecast every 30 minutes and gives you one of four states:

| State | Meaning |
|---|---|
| **Freezing now** | It's already happening |
| **Frost tonight** | Frost expected between now and 9am tomorrow |
| **Frost soon** | Frost in the forecast, but not tonight |
| **Clear** | Nothing to worry about |

Set your own frost threshold — 0°C for hard frost, 2°C if you grow anything delicate. No API keys needed, no external services. It reads the forecast data your weather integration already provides and does the worrying for you.

Works with Met Office, Met.no, OpenWeatherMap, and any weather integration that supports `weather.get_forecasts`.
