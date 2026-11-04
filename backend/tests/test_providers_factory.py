import pytest

from app.config import Settings
from app.providers.base import Providers
from app.providers.factory import REGISTRY, build_providers, resolve_names


def names(**kw):
    return resolve_names(Settings(_env_file=None, **kw))


def test_free_profile_selects_free_providers():
    assert names(provider_profile="free") == {
        "chat": "gemini", "report": "gemini", "stt": "local", "tts": "local"}


def test_paid_profile_selects_paid_providers():
    assert names(provider_profile="paid") == {
        "chat": "anthropic", "report": "anthropic", "stt": "openai", "tts": "openai"}


def test_override_beats_profile():
    n = names(provider_profile="free", tts_provider="openai")
    assert n["tts"] == "openai" and n["chat"] == "gemini" and n["stt"] == "local"


def test_unknown_provider_raises():
    with pytest.raises(ValueError):
        names(chat_provider="nope")
    with pytest.raises(ValueError):
        names(stt_provider="gemini")  # valid name, wrong role
    with pytest.raises(ValueError):
        names(provider_profile="gold")


def test_build_providers_uses_registered_builders(monkeypatch):
    built = []
    for role, name in [("chat", "gemini"), ("report", "gemini"), ("stt", "local"), ("tts", "local")]:
        monkeypatch.setitem(REGISTRY, (role, name), lambda s, r=role: built.append(r) or r)
    p = build_providers(Settings(_env_file=None))
    assert isinstance(p, Providers)
    assert built == ["chat", "report", "stt", "tts"]
    assert (p.chat, p.report, p.stt, p.tts) == ("chat", "report", "stt", "tts")


def test_build_providers_missing_builder_raises(monkeypatch):
    monkeypatch.delitem(REGISTRY, ("chat", "gemini"), raising=False)
    with pytest.raises(ValueError):
        build_providers(Settings(_env_file=None))
