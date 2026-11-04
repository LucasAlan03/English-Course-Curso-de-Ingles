from datetime import datetime, timezone

import pytest

from app import pricing
from app.db import insert
from app.errors import MonthlyCapReached, ProviderOutOfCredit
from app.providers.base import Usage
from app.usage import UsageTracker


@pytest.fixture
def tracker(conn, settings, clock):
    return UsageTracker(conn, settings, clock)


def add_cost(conn, cost, when="2026-11-03T15:00:00+00:00"):
    insert(conn, "api_usage", provider="anthropic", model="m", kind="text",
           input_units=1, output_units=1, cost_brl=cost, created_at=when)


def test_free_usage_costs_zero_and_is_logged(tracker, conn):
    assert tracker.record(Usage("gemini", "flash", "text", 1000, 500)) == 0
    assert conn.execute("SELECT COUNT(*) FROM api_usage").fetchone()[0] == 1


def test_paid_usage_uses_price_table(tracker, monkeypatch):
    monkeypatch.setitem(pricing.PRICES, ("openai", "tts-x", "tts"), (0.01, 0.0))
    cost = tracker.record(Usage("openai", "tts-x", "tts", 100, 0))
    assert cost == pytest.approx(0.01 * 100 * pricing.USD_BRL)
    assert tracker.month_total_brl() == pytest.approx(cost)


def test_month_total_sums_only_current_month(tracker, conn):
    add_cost(conn, 10.0)
    add_cost(conn, 5.0, "2026-11-30T23:00:00+00:00")
    add_cost(conn, 99.0, "2026-10-31T12:00:00+00:00")  # last month
    assert tracker.month_total_brl() == pytest.approx(15.0)


@pytest.mark.parametrize("total,level", [(44.0, "ok"), (45.0, "warn"), (49.99, "warn"), (50.0, "blocked")])
def test_status_levels(tracker, conn, total, level):
    add_cost(conn, total)
    status = tracker.status()
    assert status["level"] == level
    assert (status["warn"], status["cap"]) == (45.0, 50.0)
    assert status["total"] == pytest.approx(total)


def test_cap_blocks_paid_but_not_free(tracker, conn):
    add_cost(conn, 50.0)
    with pytest.raises(MonthlyCapReached):
        tracker.ensure_can_spend(is_paid=True)
    tracker.ensure_can_spend(is_paid=False)


def test_error_json_shape(app_client):
    def boom():
        raise ProviderOutOfCredit("openai")

    app_client.app.add_api_route("/boom", boom)
    r = app_client.get("/boom")
    assert r.status_code == 402
    body = r.json()
    assert body["error"] == "provider_out_of_credit" and body["provider"] == "openai"
    assert "openai" in body["detail"].lower()


def test_usage_route(app_client):
    r = app_client.get("/usage/month")
    assert r.status_code == 200
    assert r.json()["level"] == "ok" and r.json()["total"] == 0


def test_settings_route_reports_profile_and_providers(app_client):
    body = app_client.get("/settings").json()
    assert body["profile"] == "free"
    assert body["providers"] == {"chat": "gemini", "report": "gemini", "stt": "local", "tts": "local"}
    assert body["usage"]["level"] == "ok"
    assert "api_key" not in str(body).lower()  # never leak keys
