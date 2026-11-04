from datetime import date, datetime, timezone

from app.clock import FixedClock


def test_health_open(app_client):
    r = app_client.get("/health", headers={"X-API-Token": ""})
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_protected_requires_token(app_client):
    assert app_client.get("/home", headers={"X-API-Token": ""}).status_code == 401
    assert app_client.get("/home", headers={"X-API-Token": "wrong"}).status_code == 401


def test_fixed_clock_today_uses_tz():
    clock = FixedClock(datetime(2026, 11, 4, 2, 30, tzinfo=timezone.utc), "America/Sao_Paulo")
    assert clock.today() == date(2026, 11, 3)
