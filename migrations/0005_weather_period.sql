CREATE TABLE IF NOT EXISTS weather_cache_period (
    city_id INTEGER PRIMARY KEY,
    updated TEXT,
    morning_temp REAL,
    morning_code INTEGER,
    morning_wind REAL,
    day_temp REAL,
    day_code INTEGER,
    day_wind REAL,
    evening_temp REAL,
    evening_code INTEGER,
    evening_wind REAL,
    night_temp REAL,
    night_code INTEGER,
    night_wind REAL
);
