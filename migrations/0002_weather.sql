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
