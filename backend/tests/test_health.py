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


def test_cors_preflight_passes_without_token(app_client):
    r = app_client.options(
        "/home",
        headers={"Origin": "http://localhost:8081", "Access-Control-Request-Method": "GET",
                 "Access-Control-Request-Headers": "x-api-token", "X-API-Token": ""},
    )
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] in ("*", "http://localhost:8081")
    assert "x-api-token" in r.headers["access-control-allow-headers"].lower()


def test_error_responses_carry_cors_headers(app_client):
    r = app_client.get("/home", headers={"Origin": "http://localhost:8081", "X-API-Token": ""})
    assert r.status_code == 401 and "access-control-allow-origin" in r.headers
