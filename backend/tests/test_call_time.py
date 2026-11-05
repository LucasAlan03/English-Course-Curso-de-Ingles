from datetime import date, datetime, timedelta, timezone

from app.call_time import active_seconds, call_minutes_for_day
from app.db import insert

T0 = datetime(2026, 11, 3, 15, 0, tzinfo=timezone.utc)  # 12:00 in São Paulo


def at(seconds):
    return T0 + timedelta(seconds=seconds)


def test_gaps_are_capped_at_three_minutes():
    assert active_seconds([at(0), at(60), at(660)]) == 60 + 180


def test_unsorted_times_and_empty_lists():
    assert active_seconds([at(120), at(0)]) == 120
    assert active_seconds([]) == 0 and active_seconds([at(5)]) == 0


def session(deps, start, kind="free", messages=(), finished=None):
    sid = insert(deps.conn, "sessions", kind=kind, module_id=None, started_at=start.isoformat(),
                 finished_at=finished.isoformat() if finished else None)
    for role, when in messages:
        insert(deps.conn, "messages", session_id=sid, role=role, text="hi", created_at=when.isoformat())
    return sid


def test_session_minutes_count_active_time(deps):
    session(deps, at(0), messages=[("assistant", at(5)), ("user", at(65)), ("assistant", at(125)),
                                   ("user", at(245))], finished=at(305))
    assert call_minutes_for_day(deps, date(2026, 11, 3)) == 5


def test_session_with_only_the_opener_counts_zero(deps):
    session(deps, at(0), messages=[("assistant", at(5))], finished=at(300))
    assert call_minutes_for_day(deps, date(2026, 11, 3)) == 0


def test_writing_sessions_do_not_count(deps):
    session(deps, at(0), kind="writing", messages=[("user", at(60)), ("user", at(120))])
    assert call_minutes_for_day(deps, date(2026, 11, 3)) == 0


def test_session_late_at_night_counts_on_the_local_day(deps):
    late = datetime(2026, 11, 4, 2, 50, tzinfo=timezone.utc)  # 23:50 on 11-03 in São Paulo
    session(deps, late, messages=[("user", late + timedelta(seconds=120)), ("user", late + timedelta(seconds=240))])
    assert call_minutes_for_day(deps, date(2026, 11, 3)) == 4
    assert call_minutes_for_day(deps, date(2026, 11, 4)) == 0


def test_external_and_app_minutes_add_up(app_client, deps):
    session(deps, at(0), messages=[("user", at(120)), ("user", at(240))])
    r = app_client.post("/calls/external", json={"date": "2026-11-03", "source": "Be Confident", "minutes": 25})
    assert r.status_code == 200
    body = app_client.get("/calls", params={"date": "2026-11-03"}).json()
    assert body["app_minutes"] == 4 and body["total_minutes"] == 29
    assert body["external"][0]["source"] == "Be Confident" and body["external"][0]["minutes"] == 25


def test_external_call_validation_and_delete(app_client):
    assert app_client.post("/calls/external", json={"date": "2026-11-03", "source": "x", "minutes": 0}).status_code == 422
    assert app_client.post("/calls/external", json={"date": "2026-11-03", "source": "x", "minutes": 601}).status_code == 422
    item = app_client.post("/calls/external", json={"date": "2026-11-03", "source": "x", "minutes": 10}).json()
    assert app_client.delete(f"/calls/external/{item['id']}").status_code == 200
    assert app_client.get("/calls", params={"date": "2026-11-03"}).json()["total_minutes"] == 0
    assert app_client.delete("/calls/external/999").status_code == 404


def test_calls_summary_day_and_week(app_client):
    app_client.post("/calls/external", json={"date": "2026-11-03", "source": "a", "minutes": 10})
    app_client.post("/calls/external", json={"date": "2026-11-02", "source": "a", "minutes": 15})  # Monday
    app_client.post("/calls/external", json={"date": "2026-11-01", "source": "a", "minutes": 40})  # previous Sunday
    body = app_client.get("/calls/summary", params={"date": "2026-11-03"}).json()
    assert body == {"day_minutes": 10, "week_minutes": 25}


def test_elapsed_uses_now_as_the_last_event(app_client, deps):
    sid = session(deps, at(-300), messages=[("user", at(-240)), ("user", at(-120))])
    assert app_client.get(f"/sessions/{sid}/elapsed").json() == {"seconds": 60 + 120 + 120}
