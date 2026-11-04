import pytest

from app.config import Settings
from app.errors import ProviderAuthFailed, ProviderRateLimited, ProviderUnavailable
from app.providers.base import Msg, Usage
from app.providers.factory import build_providers
from app.providers.gemini import GeminiText
from app.providers.local_stt import LocalWhisperStt
from app.providers.local_tts import LocalTts
from sdk_fakes import AuthError, FakeGeminiClient, FakePiperVoice, FakeWhisperModel, QuotaError, ServerError


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
    stt = LocalWhisperStt(decode=lambda b: b, model=FakeWhisperModel())
    result = stt.transcribe(b"RIFF....", "audio/wav")
    assert result.text == "Hello there"
    assert result.usage == Usage("local", "faster-whisper", "stt", 2, 0)
    assert stt.is_paid is False


def test_local_stt_silence_gives_empty_text():
    stt = LocalWhisperStt(decode=lambda b: b, model=FakeWhisperModel(texts=()))
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


def stt_with(**kwargs):
    model = FakeWhisperModel(**kwargs)
    return LocalWhisperStt(decode=lambda data: data, model=model), model


def test_local_stt_detects_the_language_in_a_single_pass():
    stt, model = stt_with(probs=[("pt", 0.9), ("en", 0.05)])
    assert stt.transcribe(b"x", "audio/wav").text == "Hello there"
    assert len(model.calls) == 1 and model.calls[0]["language"] is None


def test_local_stt_uses_fast_greedy_decoding():
    stt, model = stt_with()
    stt.transcribe(b"x", "audio/wav")
    assert model.calls[0]["beam_size"] == 1 and model.calls[0]["vad_filter"] is True
    assert model.calls[0]["condition_on_previous_text"] is False


def test_local_stt_retries_in_pt_or_en_when_another_language_is_detected():
    stt, model = stt_with(probs=[("es", 0.6), ("pt", 0.2), ("en", 0.15)])
    stt.transcribe(b"x", "audio/wav")
    assert [c["language"] for c in model.calls] == [None, "pt"]


def test_local_stt_prefers_english_when_pt_and_en_are_close():
    stt, model = stt_with(probs=[("es", 0.5), ("en", 0.25), ("pt", 0.24)])
    stt.transcribe(b"x", "audio/wav")
    assert [c["language"] for c in model.calls] == [None, "en"]


def test_local_stt_defaults_to_english_without_probabilities():
    stt, model = stt_with(probs=[("es", 0.9)])
    stt.transcribe(b"x", "audio/wav")
    assert [c["language"] for c in model.calls] == [None, "en"]


def test_whisper_model_default_is_small_for_better_accuracy():
    assert Settings(_env_file=None).whisper_model_size == "small"


# --- Gemini: less thinking and a fallback model -------------------------------------------------

def test_gemini_sends_the_thinking_level_when_configured():
    client = FakeGeminiClient()
    GeminiText("k", "m", client=client, thinking_level="minimal").generate("s", [Msg("user", "x")])
    assert client.calls[0]["config"]["thinking_config"] == {"thinking_level": "minimal"}


def test_gemini_sends_no_thinking_config_by_default():
    client = FakeGeminiClient()
    GeminiText("k", "m", client=client).generate("s", [Msg("user", "x")])
    assert "thinking_config" not in client.calls[0]["config"]


def test_gemini_falls_back_to_another_model_when_the_first_stays_overloaded():
    client = FakeGeminiClient("from fallback", errors=[ServerError("503"), ServerError("503")])
    model = GeminiText("k", "main", client=client, fallback_model="backup", sleep=lambda s: None)
    result = model.generate("s", [Msg("user", "x")])
    assert result.text == "from fallback" and result.usage.model == "backup"
    assert [c["model"] for c in client.calls] == ["main", "main", "backup"]


def test_gemini_raises_when_the_fallback_is_overloaded_too():
    client = FakeGeminiClient(errors=[ServerError("503")] * 3)
    model = GeminiText("k", "main", client=client, fallback_model="backup", sleep=lambda s: None)
    with pytest.raises(ProviderUnavailable):
        model.generate("s", [Msg("user", "x")])


def test_gemini_never_falls_back_on_auth_errors():
    client = FakeGeminiClient(errors=[AuthError("API key not valid")])
    model = GeminiText("k", "main", client=client, fallback_model="backup", sleep=lambda s: None)
    with pytest.raises(ProviderAuthFailed):
        model.generate("s", [Msg("user", "x")])
    assert len(client.calls) == 1


def test_factory_passes_thinking_and_fallback_settings_to_gemini():
    settings = Settings(_env_file=None, gemini_fallback_model="backup-model")
    providers = build_providers(settings)
    assert providers.chat.thinking_level == "minimal" and providers.report.thinking_level == "low"
    assert providers.chat.fallback_model == providers.report.fallback_model == "backup-model"

