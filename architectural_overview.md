# Architectural Overview

This document outlines the main components of the Telegram scheduler bot.

## 1 Introduction
The bot forwards posts to channels at scheduled times. It stores users, channels and schedule data in a SQLite database.

## 2 Database
The database is migrated via SQL files in the `migrations` folder.

## 3 Services
### 3.1 Bot
Handles Telegram updates and user commands.

### 3.2 WeatherService

Collects current weather data from Open-Meteo for registered cities each hour. Results are stored in `weather_cache` and logged. Failed requests are retried up to three times with a minute pause, after which the service waits until the next hour. The bot ignores API errors so it continues running.


### 3.3 Webhook
The HTTP server receives Telegram webhooks.

### 3.4 Authorization
Superadmins approve or reject new users.

### 3.5 Scheduler
A background loop processes scheduled posts and weather jobs at regular intervals defined by `SCHED_INTERVAL_SEC`.

## 4 Deployment
The application targets Fly.io free tier and runs a single process.

## 5 User Stories
- US-1..US-9: base bot functionality (registration, scheduling, buttons).
- US-10: admin adds a city.
- US-11: admin views and removes cities.
- US-12: periodic weather collection from Open-Meteo.
- US-13: admin requests last weather check info and can force an update.
- US-14: admin registers a weather post for updates.
- US-15: automatic weather post updates.
- US-16: admin lists registered posts.
