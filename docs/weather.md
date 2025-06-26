# Weather Extension

This document describes the weather feature set for the Telegram scheduler bot.

Weather for each city is queried from the Open-Meteo API approximately once per

hour and stored in the `weather_cache` table. The bot logs both the raw HTTP
response and the parsed weather information. The request looks like:

```
https://api.open-meteo.com/v1/forecast?latitude=<lat>&longitude=<lon>&current=temperature_2m,weather_code,wind_speed_10m
```

The bot continues working even if a query fails. When a request fails, it is
retried up to three times with a one‑minute pause between attempts. After that,
no further requests are made for that city until the next scheduled hour.



## Commands

- `/addcity <name> <lat> <lon>` – add a city to the database. Only superadmins can
  execute this command. Latitude and longitude must be valid floating point numbers
  and may include six or more digits after the decimal point.
- `/cities` – list registered cities. Each entry has an inline *Delete* button that
  removes the city from the list. Coordinates are displayed with six decimal digits
  to reflect the stored precision.
- `/weather` – show the last collected weather for all cities. Only superadmins may

  request this information. Append `now` to force a fresh API request before
  displaying results.



## Database schema

```
CREATE TABLE IF NOT EXISTS cities (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    UNIQUE(name)
);

CREATE TABLE IF NOT EXISTS weather_cache_day (
    city_id INTEGER NOT NULL,
    day DATE NOT NULL,
    temperature REAL,
    weather_code INTEGER,
    wind_speed REAL,
    PRIMARY KEY (city_id, day)
);

CREATE TABLE IF NOT EXISTS weather_cache_hour (
    city_id INTEGER NOT NULL,
    timestamp DATETIME NOT NULL,
    temperature REAL,
    weather_code INTEGER,
    wind_speed REAL,
    PRIMARY KEY (city_id, timestamp)
);



CREATE TABLE IF NOT EXISTS weather_posts (
    id INTEGER PRIMARY KEY,
    chat_id BIGINT NOT NULL,
    message_id BIGINT NOT NULL,
    city_id INTEGER NOT NULL,
    UNIQUE(chat_id, message_id)
);
```

## Open-Meteo example response

```json
{
  "latitude": 55.75,
  "longitude": 37.62,
  "current": {
    "temperature_2m": 20.5,
    "weather_code": 1,
    "wind_speed_10m": 3.5
  }
}
```

## WMO code to emoji

| Code | Emoji |
|-----:|:------|
| 0 | ☀️ |
| 1 | 🌤 |
| 2 | ⛅ |
| 3 | ☁️ |
| 45 | 🌫 |
| 48 | 🌫 |
| 51 | 🌦 |
| 53 | 🌦 |
| 55 | 🌦 |
| 61 | 🌧 |
| 63 | 🌧 |
| 65 | 🌧 |
| 71 | ❄️ |
| 73 | ❄️ |
| 75 | ❄️ |
| 80 | 🌦 |
| 81 | 🌦 |
| 82 | 🌧 |
| 95 | ⛈ |
| 96 | ⛈ |
| 99 | ⛈ |
```
