from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.clock import FixedClock
from app.config import Settings
from app.main import create_app
from app.providers.base import Providers
from app.providers.fakes import FakeStt, FakeTextModel, FakeTts

TEST_TOKEN = "test-token"


@pytest.fixture
def settings(tmp_path) -> Settings:
    return Settings(
        api_token=TEST_TOKEN,
        data_dir=str(tmp_path / "data"),
        _env_file=None,
    )


@pytest.fixture
def clock() -> FixedClock:
    return FixedClock(datetime(2026, 11, 3, 15, 0, tzinfo=timezone.utc), "America/Sao_Paulo")


@pytest.fixture
def providers() -> Providers:
    return Providers(chat=FakeTextModel(), report=FakeTextModel(), stt=FakeStt(), tts=FakeTts())


@pytest.fixture
def app_client(settings, clock, providers) -> TestClient:
    app = create_app(settings, providers=providers, clock=clock)
    return TestClient(app, headers={"X-API-Token": TEST_TOKEN})


@pytest.fixture
def conn(tmp_path):
    from app.db import connect, init_schema

    c = connect(str(tmp_path / "test.db"))
    init_schema(c)
    return c


@pytest.fixture
def tracker(conn, settings, clock):
    from app.usage import UsageTracker

    return UsageTracker(conn, settings, clock)
