import pytest

from app.config import Settings
from app.errors import ProviderRateLimited
from app.providers.base import Msg, Usage
from app.providers.factory import build_providers
from app.providers.gemini import GeminiText
from app.providers.local_stt import LocalWhisperStt
from app.providers.local_tts import LocalTts
from sdk_fakes import FakeGeminiClient, FakePiperVoice, FakeWhisperModel, QuotaError


def gemini(client, sleeps=None):
    sleeps = sleeps if sleeps is not None else []
    return GeminiText("key", "gem-model", client=client, sleep=sleeps.append, retry_wait=5.0)


def test_gemini_returns_text_and_usage_and_maps_roles():
    client = FakeGeminiClient("pong")
    result = gemini(client).generate("be nice", [Msg("user", "ping"), Msg("assistant", "pong?")], json_mode=True)
    assert result.text == "pong"
    assert result.usage == Usage("gemini", "gem-model", "text", 10, 5)
    call = client.calls[0]
    assert call["model"] == "gem-model"
    assert [c["role"] for c in call["contents"]] == ["user", "model"]
    assert call["contents"][0]["parts"][0]["text"] == "ping"
    assert call["config"]["system_instruction"] == "be nice"
    assert call["config"]["response_mime_type"] == "application/json"


def test_gemini_plain_text_has_no_json_mime():
    client = FakeGeminiClient()
    gemini(client).generate("s", [Msg("user", "x")])
    assert "response_mime_type" not in client.calls[0]["config"]


def test_gemini_retries_once_on_quota_then_succeeds():
    client = FakeGeminiClient("ok", errors=[QuotaError("RESOURCE_EXHAUSTED")])
    sleeps = []
    assert gemini(client, sleeps).generate("s", [Msg("user", "x")]).text == "ok"
    assert sleeps == [5.0] and len(client.calls) == 2


def test_gemini_maps_quota_error_to_rate_limited():
    client = FakeGeminiClient(errors=[QuotaError("quota"), QuotaError("quota")])
    with pytest.raises(ProviderRateLimited) as exc:
        gemini(client).generate("s", [Msg("user", "x")])
    assert exc.value.code == "provider_rate_limited" and exc.value.extra["provider"] == "gemini"


def test_gemini_other_errors_propagate():
    client = FakeGeminiClient(errors=[ValueError("boom")])
    with pytest.raises(ValueError):
        gemini(client).generate("s", [Msg("user", "x")])


def test_local_stt_returns_text_and_seconds():
    stt = LocalWhisperStt(model=FakeWhisperModel())
    result = stt.transcribe(b"RIFF....", "audio/wav")
    assert result.text == "Hello there"
    assert result.usage == Usage("local", "faster-whisper", "stt", 2, 0)
    assert stt.is_paid is False


def test_local_stt_silence_gives_empty_text():
    stt = LocalWhisperStt(model=FakeWhisperModel(texts=()))
    assert stt.transcribe(b"x", "audio/wav").text == ""


def test_local_tts_returns_wav_bytes():
    tts = LocalTts(voice=FakePiperVoice())
    result = tts.synthesize("hello")
    assert result.audio[:4] == b"RIFF" and result.mime == "audio/wav"
    assert result.usage == Usage("local", "piper", "tts", 5, 0)


def test_local_tts_missing_voice_file_gives_clear_error(tmp_path):
    tts = LocalTts(voice_path=str(tmp_path / "missing.onnx"))
    with pytest.raises(RuntimeError, match="missing.onnx"):
        tts.synthesize("hello")


def test_free_profile_builds_without_network_or_models():
    providers = build_providers(Settings(_env_file=None, provider_profile="free"))
    assert isinstance(providers.chat, GeminiText) and providers.chat.model != providers.report.model
    assert isinstance(providers.stt, LocalWhisperStt) and isinstance(providers.tts, LocalTts)
    assert not any(p.is_paid for p in (providers.chat, providers.report, providers.stt, providers.tts))
