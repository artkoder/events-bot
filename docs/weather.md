# Weather Extension

This document describes the weather feature set for the Telegram scheduler bot.


## Commands

- `/addcity <name> <lat> <lon>` – add a city to the database. Only superadmins can execute this command. Latitude and longitude must be valid floating point numbers.
- `/cities` – list registered cities. Each entry has an inline *Delete* button that removes the city from the list.


## Database schema

```
CREATE TABLE IF NOT EXISTS cities (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    UNIQUE(name)
);

CREATE TABLE IF NOT EXISTS weather_cache (
    id INTEGER PRIMARY KEY,
    city_id INTEGER NOT NULL,
    fetched_at DATETIME NOT NULL,
    provider TEXT NOT NULL,
    period TEXT NOT NULL,
    temp REAL,
    wmo_code INTEGER,
    wind REAL,
    UNIQUE(city_id, period, DATE(fetched_at))
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
