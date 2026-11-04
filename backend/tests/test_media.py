import pytest

BASE = {"date": "2026-11-03", "type": "watch", "category": "series", "title": "Friends",
        "episode": "S01E02", "minutes": 22}


def add(app_client, **overrides):
    return app_client.post("/media", json={**BASE, **overrides})


def test_create_and_list_by_date(app_client):
    created = add(app_client)
    assert created.status_code == 200 and created.json()["id"] > 0
    assert created.json()["title"] == "Friends" and created.json()["episode"] == "S01E02"
    add(app_client, date="2026-11-02", title="Other day")
    listed = app_client.get("/media", params={"date": "2026-11-03"}).json()
    assert [m["title"] for m in listed] == ["Friends"]


def test_multiple_items_same_day(app_client):
    add(app_client)
    add(app_client, category="podcast", title="Lex", episode=None, minutes=60)
    add(app_client, type="read", category="hq", title="Maus", episode=None, minutes=15, pages=12)
    assert len(app_client.get("/media", params={"date": "2026-11-03"}).json()) == 3


@pytest.mark.parametrize("minutes", [0, -5, 1441, 2000])
def test_invalid_minutes_rejected(app_client, minutes):
    assert add(app_client, minutes=minutes).status_code == 422


@pytest.mark.parametrize("bad", [
    {"date": "2026-13-45"}, {"date": "tomorrow"}, {"date": ""},
    {"type": "listen"}, {"title": "   "}, {"pages": 0},
])
def test_invalid_fields_rejected(app_client, bad):
    assert add(app_client, **bad).status_code == 422


def test_category_must_match_type(app_client):
    assert add(app_client, type="watch", category="hq").status_code == 422
    assert add(app_client, type="read", category="series", episode=None).status_code == 422
    assert add(app_client, type="read", category="book", episode=None).status_code == 200


def seed(app_client):
    add(app_client, minutes=22)                                   # Tue, series
    add(app_client, minutes=25)                                   # Tue, series
    add(app_client, type="read", category="hq", title="Maus", episode=None, minutes=15)
    add(app_client, date="2026-11-02", category="podcast", title="Pod", episode=None, minutes=30)  # Mon
    add(app_client, date="2026-11-01", category="video", title="Vid", episode=None, minutes=40)    # previous Sun
    add(app_client, date="2026-10-31", category="movie", title="Film", episode=None, minutes=100)  # previous month


def test_summary_totals_by_day_week_month(app_client):
    seed(app_client)
    body = app_client.get("/media/summary", params={"date": "2026-11-03"}).json()
    assert body["day"] == {"total_minutes": 62, "by_type": {"watch": 47, "read": 15},
                           "by_category": {"series": 47, "hq": 15}}
    assert body["week"]["total_minutes"] == 92  # Monday 11-02 up to Sunday 11-08
    assert body["week"]["by_category"] == {"series": 47, "hq": 15, "podcast": 30}
    assert body["month"]["total_minutes"] == 132  # all of November, not 10-31


def test_summary_defaults_to_today_and_handles_empty(app_client):
    body = app_client.get("/media/summary").json()
    assert body["day"] == {"total_minutes": 0, "by_type": {}, "by_category": {}}


def test_update_and_delete_change_totals(app_client):
    item = add(app_client, minutes=20).json()
    changed = app_client.put(f"/media/{item['id']}", json={**BASE, "minutes": 50, "title": "Friends 2"})
    assert changed.status_code == 200 and changed.json()["title"] == "Friends 2"
    assert app_client.get("/media/summary", params={"date": "2026-11-03"}).json()["day"]["total_minutes"] == 50
    assert app_client.delete(f"/media/{item['id']}").status_code == 200
    assert app_client.get("/media/summary", params={"date": "2026-11-03"}).json()["day"]["total_minutes"] == 0
    assert app_client.get("/media", params={"date": "2026-11-03"}).json() == []


def test_update_with_invalid_data_keeps_the_old_values(app_client):
    item = add(app_client, minutes=20).json()
    assert app_client.put(f"/media/{item['id']}", json={**BASE, "minutes": 0}).status_code == 422
    assert app_client.get("/media", params={"date": "2026-11-03"}).json()[0]["minutes"] == 20


def test_unknown_item_404(app_client):
    assert app_client.put("/media/999", json=BASE).status_code == 404
    assert app_client.delete("/media/999").status_code == 404


def test_media_marks_the_daily_pillars(app_client):
    assert app_client.get("/home").json()["pillars"]["watch"] is False
    add(app_client)
    assert app_client.get("/home").json()["pillars"]["watch"] is True
