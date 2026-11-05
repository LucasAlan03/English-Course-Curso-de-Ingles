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
def module_dir(tmp_path):
    from builders import write_module

    directory = tmp_path / "modules"
    directory.mkdir()
    write_module(directory, "b1_past_simple_continuous", "B1", 1, "Past simple x past continuous")
    write_module(directory, "b1_futures", "B1", 2, "Futures")
    write_module(directory, "b2_passive_voice", "B2", 1, "Passive voice")
    return directory


@pytest.fixture
def exercises_dir(tmp_path):
    from builders import write_exercises

    directory = tmp_path / "exercises"
    directory.mkdir()
    write_exercises(directory, "b1_past_simple_continuous")
    return directory


@pytest.fixture
def exams_dir(tmp_path):
    from builders import valid_exam, write_exam

    directory = tmp_path / "exams"
    directory.mkdir()
    write_exam(directory, "B1", valid_exam(["b1_past_simple_continuous", "b1_futures"]))
    return directory


@pytest.fixture
def settings(tmp_path, module_dir, exercises_dir, exams_dir) -> Settings:
    return Settings(
        api_token=TEST_TOKEN,
        data_dir=str(tmp_path / "data"),
        content_dir=str(module_dir),
        exercises_dir=str(exercises_dir),
        exams_dir=str(exams_dir),
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


@pytest.fixture
def deps(app_client):
    return app_client.app.state.deps
