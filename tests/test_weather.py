import os
import sys
import json
from datetime import datetime, timedelta
import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from main import Bot

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "dummy")

@pytest.mark.asyncio
async def test_add_list_delete_city(tmp_path):
    bot = Bot("dummy", str(tmp_path / "db.sqlite"))

    calls = []

    async def dummy(method, data=None):
        calls.append((method, data))
        return {"ok": True}

    bot.api_request = dummy  # type: ignore
    await bot.start()

    await bot.handle_update({"message": {"text": "/start", "from": {"id": 1}}})

    await bot.handle_update({"message": {"text": "/addcity Paris 48.85 2.35", "from": {"id": 1}}})
    cur = bot.db.execute("SELECT name FROM cities")
    row = cur.fetchone()
    assert row and row["name"] == "Paris"

    await bot.handle_update({"message": {"text": "/cities", "from": {"id": 1}}})
    last = calls[-1]
    assert last[0] == "sendMessage"

    assert "48.850000" in last[1]["text"] and "2.350000" in last[1]["text"]

    cb = last[1]["reply_markup"]["inline_keyboard"][0][0]["callback_data"]
    cid = int(cb.split(":")[1])

    await bot.handle_update({"callback_query": {"from": {"id": 1}, "data": cb, "message": {"chat": {"id": 1}, "message_id": 10}, "id": "q"}})
    cur = bot.db.execute("SELECT * FROM cities WHERE id=?", (cid,))
    assert cur.fetchone() is None
    assert any(c[0] == "editMessageReplyMarkup" for c in calls)

    await bot.close()


@pytest.mark.asyncio
async def test_collect_and_report_weather(tmp_path):
    bot = Bot("dummy", str(tmp_path / "db.sqlite"))

    api_calls = []

    async def dummy(method, data=None):
        api_calls.append((method, data))
        return {"ok": True}

    bot.api_request = dummy  # type: ignore

    async def fetch_dummy(lat, lon):
        return {"current": {"temperature_2m": 10.0, "weather_code": 1, "wind_speed_10m": 3.0}}

    bot.fetch_open_meteo = fetch_dummy  # type: ignore

    await bot.start()

    await bot.handle_update({"message": {"text": "/start", "from": {"id": 1}}})
    bot.db.execute("INSERT INTO cities (id, name, lat, lon) VALUES (1, 'Paris', 48.85, 2.35)")
    bot.db.commit()

    await bot.collect_weather()


    cur = bot.db.execute("SELECT temperature, weather_code FROM weather_cache_hour WHERE city_id=1")
    row = cur.fetchone()
    assert row and row["temperature"] == 10.0 and row["weather_code"] == 1


    await bot.handle_update({"message": {"text": "/weather", "from": {"id": 1}}})
    assert api_calls[-1][0] == "sendMessage"
    assert "Paris" in api_calls[-1][1]["text"]

    await bot.close()



@pytest.mark.asyncio
async def test_weather_upsert(tmp_path):
    bot = Bot("dummy", str(tmp_path / "db.sqlite"))

    async def fetch1(lat, lon):
        return {"current": {"temperature_2m": 1.0, "weather_code": 1, "wind_speed_10m": 1.0}}

    async def fetch2(lat, lon):
        return {"current": {"temperature_2m": 2.0, "weather_code": 1, "wind_speed_10m": 1.0}}

    bot.fetch_open_meteo = fetch1  # type: ignore

    await bot.start()

    await bot.handle_update({"message": {"text": "/start", "from": {"id": 1}}})
    bot.db.execute("INSERT INTO cities (id, name, lat, lon) VALUES (1, 'Paris', 48.85, 2.35)")
    bot.db.commit()

    await bot.collect_weather()

    bot.fetch_open_meteo = fetch2  # type: ignore
    await bot.collect_weather()

    cur = bot.db.execute("SELECT temperature FROM weather_cache_day WHERE city_id=1")
    row = cur.fetchone()
    assert row and row["temperature"] == 2.0

    await bot.close()


@pytest.mark.asyncio
async def test_weather_now_forces_fetch(tmp_path):
    bot = Bot("dummy", str(tmp_path / "db.sqlite"))

    api_calls = []
    async def dummy(method, data=None):
        api_calls.append((method, data))
        return {"ok": True}

    bot.api_request = dummy  # type: ignore

    count = 0
    async def fetch_dummy(lat, lon):
        nonlocal count
        count += 1
        return {"current": {"temperature_2m": 5.0, "weather_code": 2, "wind_speed_10m": 1.0}}

    bot.fetch_open_meteo = fetch_dummy  # type: ignore

    await bot.start()

    await bot.handle_update({"message": {"text": "/start", "from": {"id": 1}}})
    bot.db.execute("INSERT INTO cities (id, name, lat, lon) VALUES (1, 'Rome', 41.9, 12.5)")
    bot.db.commit()

    await bot.handle_update({"message": {"text": "/weather now", "from": {"id": 1}}})
    assert count == 1
    assert api_calls[-1][0] == "sendMessage"

    await bot.close()


@pytest.mark.asyncio
async def test_weather_retry_logic(tmp_path):
    bot = Bot("dummy", str(tmp_path / "db.sqlite"))

    count = 0
    async def fetch_fail(lat, lon):
        nonlocal count
        count += 1
        return None

    bot.fetch_open_meteo = fetch_fail  # type: ignore

    await bot.start()

    await bot.handle_update({"message": {"text": "/start", "from": {"id": 1}}})
    bot.db.execute("INSERT INTO cities (id, name, lat, lon) VALUES (1, 'Rome', 41.9, 12.5)")
    bot.db.commit()

    await bot.collect_weather()
    assert count == 1
    # second call within a minute should not trigger another request
    await bot.collect_weather()
    assert count == 1

    # pretend one minute passed
    attempts, ts = bot.failed_fetches[1]
    bot.failed_fetches[1] = (attempts, ts - timedelta(minutes=1, seconds=1))
    await bot.collect_weather()
    assert count == 2

    # set three attempts in last second, should skip
    bot.failed_fetches[1] = (3, datetime.utcnow())
    await bot.collect_weather()
    assert count == 2

    # after thirty minutes allowed again
    bot.failed_fetches[1] = (3, datetime.utcnow() - timedelta(minutes=31))
    await bot.collect_weather()
    assert count == 3

    await bot.close()


@pytest.mark.asyncio
async def test_register_weather_post(tmp_path):
    bot = Bot("dummy", str(tmp_path / "db.sqlite"))

    api_calls = []
    async def dummy(method, data=None):
        api_calls.append((method, data))
        if method == "forwardMessage":

            return {
                "ok": True,
                "result": {
                    "message_id": 99,
                    "text": "orig",
                    "reply_markup": {"inline_keyboard": [[{"text": "b", "url": "u"}]]},
                },
            }

        return {"ok": True, "result": {"message_id": 1}}

    bot.api_request = dummy  # type: ignore

    async def fetch_dummy(lat, lon):
        return {"current": {"temperature_2m": 15.0, "weather_code": 1, "wind_speed_10m": 2.0}}

    bot.fetch_open_meteo = fetch_dummy  # type: ignore

    await bot.start()

    await bot.handle_update({"message": {"text": "/start", "from": {"id": 1}}})
    await bot.handle_update({"message": {"text": "/addcity Paris 48.85 2.35", "from": {"id": 1}}})

    await bot.handle_update({"message": {"text": "/regweather https://t.me/c/123/5 Paris {1|temperature}", "from": {"id": 1}}})


    cur = bot.db.execute(
        "SELECT chat_id, message_id, template, base_text, base_caption, reply_markup FROM weather_posts"
    )

    row = cur.fetchone()
    assert row and row["chat_id"] == -100123 and row["message_id"] == 5
    assert row["template"] == "Paris {1|temperature}"
    assert row["base_text"] == "orig"

    assert row["base_caption"] is None
    assert json.loads(row["reply_markup"])["inline_keyboard"][0][0]["text"] == "b"

    await bot.collect_weather()
    assert any(c[0] == "editMessageText" for c in api_calls)
    payload = [c[1] for c in api_calls if c[0] == "editMessageText"][0]
    assert payload["reply_markup"]["inline_keyboard"][0][0]["url"] == "u"

    await bot.handle_update({"message": {"text": "/weatherposts update", "from": {"id": 1}}})

    assert api_calls[-2][0] == "editMessageText"
    msg = api_calls[-1]
    assert msg[0] == "sendMessage"
    assert "https://t.me/c/123/5" in msg[1]["text"]
    assert "15.0" in msg[1]["text"]


    await bot.close()


@pytest.mark.asyncio
async def test_register_weather_post_caption(tmp_path):
    bot = Bot("dummy", str(tmp_path / "db.sqlite"))

    api_calls = []

    async def dummy(method, data=None):
        api_calls.append((method, data))
        if method == "forwardMessage":

            return {
                "ok": True,
                "result": {
                    "message_id": 99,
                    "caption": "orig cap",
                    "reply_markup": {"inline_keyboard": [[{"text": "b2", "url": "u2"}]]},
                },
            }

        return {"ok": True, "result": {"message_id": 1}}

    bot.api_request = dummy  # type: ignore

    async def fetch_dummy(lat, lon):
        return {"current": {"temperature_2m": 15.0, "weather_code": 1, "wind_speed_10m": 2.0}}

    bot.fetch_open_meteo = fetch_dummy  # type: ignore

    await bot.start()

    await bot.handle_update({"message": {"text": "/start", "from": {"id": 1}}})
    await bot.handle_update({"message": {"text": "/addcity Paris 48.85 2.35", "from": {"id": 1}}})

    await bot.handle_update({"message": {"text": "/regweather https://t.me/c/123/5 Paris {1|temperature}", "from": {"id": 1}}})

    cur = bot.db.execute(

        "SELECT base_text, base_caption, reply_markup FROM weather_posts"

    )
    row = cur.fetchone()
    assert row["base_text"] is None
    assert row["base_caption"] == "orig cap"

    assert json.loads(row["reply_markup"])["inline_keyboard"][0][0]["text"] == "b2"

    await bot.collect_weather()
    assert any(c[0] == "editMessageCaption" for c in api_calls)
    payload = [c[1] for c in api_calls if c[0] == "editMessageCaption"][0]
    assert payload["reply_markup"]["inline_keyboard"][0][0]["url"] == "u2"


    await bot.close()


@pytest.mark.asyncio
async def test_regweather_strips_header(tmp_path):
    bot = Bot("dummy", str(tmp_path / "db.sqlite"))

    async def dummy(method, data=None):
        if method == "forwardMessage":
            return {
                "ok": True,
                "result": {
                    "message_id": 99,
                    "text": "old\u2219orig"
                },
            }
        return {"ok": True, "result": {"message_id": 1}}

    bot.api_request = dummy  # type: ignore

    await bot.start()
    await bot.handle_update({"message": {"text": "/start", "from": {"id": 1}}})

    await bot.handle_update({"message": {"text": "/regweather https://t.me/c/1/1 t {1|temperature}", "from": {"id": 1}}})

    row = bot.db.execute("SELECT base_text FROM weather_posts").fetchone()
    assert row["base_text"] == "orig"


    await bot.close()

