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
    template TEXT NOT NULL,
    base_text TEXT,
    base_caption TEXT,
    reply_markup TEXT,
    UNIQUE(chat_id, message_id)
);
