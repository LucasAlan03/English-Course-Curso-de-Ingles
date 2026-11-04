from fastapi.testclient import TestClient

from app.providers.base import Providers
from app.providers.fakes import FakeStt, FakeTextModel, FakeTts
from app.smoke import run_smoke


def providers(**overrides):
    base = dict(chat=FakeTextModel(["OK"]), report=FakeTextModel(["OK"]), stt=FakeStt("hello there"), tts=FakeTts())
    return Providers(**{**base, **overrides})


def test_smoke_reports_ok_for_every_provider(tracker):
    results = run_smoke(providers(), tracker)
    assert [name for name, _, _ in results] == ["chat", "report", "stt", "tts"]
    assert all(ok for _, ok, _ in results)


def test_smoke_reports_each_failure_without_stopping(tracker):
    class Broken:
        is_paid = False

        def generate(self, *args, **kwargs):
            raise RuntimeError("no api key")

    results = dict((name, (ok, msg)) for name, ok, msg in run_smoke(providers(chat=Broken()), tracker))
    assert results["chat"][0] is False and "no api key" in results["chat"][1]
    assert results["report"][0] is True and results["tts"][0] is True


def test_smoke_flags_a_transcription_that_does_not_match(tracker):
    ok, message = {n: (o, m) for n, o, m in run_smoke(providers(stt=FakeStt("something else")), tracker)}["stt"]
    assert ok is False and "something else" in message


def test_server_factory_builds_a_working_app(monkeypatch, tmp_path):
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("API_TOKEN", "secret")
    monkeypatch.setenv("PROVIDER_PROFILE", "free")
    monkeypatch.setenv("WARM_UP", "false")
    from app.server import app_factory

    client = TestClient(app_factory(), headers={"X-API-Token": "secret"})
    assert client.get("/health").json() == {"status": "ok"}
    body = client.get("/modules").json()
    assert sum(level["total"] for level in body["levels"]) == 26
    assert client.get("/home").json()["next_module"]["id"] == "b1_past_simple_continuous"
