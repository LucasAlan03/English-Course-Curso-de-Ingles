from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.clock import FixedClock
from app.config import Settings
from app.main import create_app

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
def app_client(settings, clock) -> TestClient:
    app = create_app(settings, clock=clock)
    return TestClient(app, headers={"X-API-Token": TEST_TOKEN})
