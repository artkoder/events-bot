import os
import sys
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

    cur = bot.db.execute("SELECT temp, wmo_code FROM weather_cache WHERE city_id=1")
    row = cur.fetchone()
    assert row and row["temp"] == 10.0 and row["wmo_code"] == 1

    await bot.handle_update({"message": {"text": "/weather", "from": {"id": 1}}})
    assert api_calls[-1][0] == "sendMessage"
    assert "Paris" in api_calls[-1][1]["text"]

    await bot.close()
