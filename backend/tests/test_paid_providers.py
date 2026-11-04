import pytest

from app import pricing
from app.config import Settings
from app.errors import InvalidAIOutput, ProviderOutOfCredit, ProviderRateLimited
from app.providers.anthropic_provider import AnthropicText
from app.providers.base import Msg, Usage
from app.providers.factory import build_providers
from app.providers.openai_provider import OpenAIStt, OpenAITts
from sdk_fakes import (BillingError, FakeAnthropicClient, FakeOpenAIClient, InsufficientQuota,
                       PlainRateLimit)


def claude(client, effort="low"):
    return AnthropicText("key", "claude-haiku-5-5", effort=effort, client=client)


def test_anthropic_returns_text_only_and_usage():
    client = FakeAnthropicClient("hello!")
    result = claude(client).generate(
        "be nice", [Msg("user", "hi"), Msg("assistant", "hey"), Msg("user", "yo")])
    assert result.text == "hello!"
    assert result.usage == Usage("anthropic", "claude-haiku-5-5", "text", 12, 7)
    call = client.calls[0]
    assert call["model"] == "claude-haiku-5-5" and call["system"] == "be nice"
    assert call["messages"] == [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hey"},
        {"role": "user", "content": "yo"},
    ]
    assert call["output_config"] == {"effort": "low"} and call["max_tokens"] > 0


def test_anthropic_empty_effort_omits_output_config():
    client = FakeAnthropicClient()
    claude(client, effort="").generate("s", [Msg("user", "x")])
    assert "output_config" not in client.calls[0]


def test_anthropic_billing_error_is_out_of_credit():
    client = FakeAnthropicClient(errors=[BillingError("Your credit balance is too low")])
    with pytest.raises(ProviderOutOfCredit) as exc:
        claude(client).generate("s", [Msg("user", "x")])
    assert exc.value.extra["provider"] == "anthropic"


def test_anthropic_rate_limit_is_mapped():
    client = FakeAnthropicClient(errors=[PlainRateLimit("slow down")])
    with pytest.raises(ProviderRateLimited):
        claude(client).generate("s", [Msg("user", "x")])


def test_anthropic_refusal_is_invalid_output():
    with pytest.raises(InvalidAIOutput):
        claude(FakeAnthropicClient("", stop_reason="refusal")).generate("s", [Msg("user", "x")])


def test_openai_stt_returns_text_and_estimated_seconds():
    client = FakeOpenAIClient("good morning")
    stt = OpenAIStt("key", "gpt-4o-mini-transcribe", client=client)
    result = stt.transcribe(b"x" * 24000, "audio/webm")
    assert result.text == "good morning" and result.usage.kind == "stt"
    assert result.usage.provider == "openai" and result.usage.input_units >= 1
    kwargs = client.calls[0][1]
    assert kwargs["model"] == "gpt-4o-mini-transcribe"
    assert kwargs["file"][1] == b"x" * 24000 and kwargs["file"][2] == "audio/webm"


def test_openai_tts_returns_audio_and_chars():
    client = FakeOpenAIClient(audio=b"RIFFaudio")
    tts = OpenAITts("key", "gpt-4o-mini-tts", "alloy", client=client)
    result = tts.synthesize("hello")
    assert result.audio == b"RIFFaudio" and result.mime == "audio/wav"
    assert result.usage == Usage("openai", "gpt-4o-mini-tts", "tts", 5, 0)
    kwargs = client.calls[0][1]
    assert kwargs["voice"] == "alloy" and kwargs["input"] == "hello"


def test_openai_insufficient_quota_is_out_of_credit_but_plain_429_is_rate_limit():
    stt = OpenAIStt("k", "m", client=FakeOpenAIClient(errors=[InsufficientQuota("insufficient_quota")]))
    with pytest.raises(ProviderOutOfCredit):
        stt.transcribe(b"x", "audio/wav")
    tts = OpenAITts("k", "m", "alloy", client=FakeOpenAIClient(errors=[PlainRateLimit("rate")]))
    with pytest.raises(ProviderRateLimited):
        tts.synthesize("hi")


def test_pricing_known_models_are_priced():
    haiku = pricing.cost_brl(Usage("anthropic", "claude-haiku-5-5", "text", 1_000_000, 1_000_000))
    assert haiku == pytest.approx((0.10 + 0.50) * pricing.USD_BRL)
    stt = pricing.cost_brl(Usage("openai", "gpt-4o-mini-transcribe", "stt", 60, 0))
    assert stt == pytest.approx(0.003 * pricing.USD_BRL)


def test_pricing_unknown_paid_model_uses_most_expensive_known_rate():
    unknown = pricing.cost_brl(Usage("anthropic", "claude-mystery", "text", 1_000_000, 0))
    sonnet = pricing.cost_brl(Usage("anthropic", "claude-sonnet-5-5", "text", 1_000_000, 0))
    assert unknown == pytest.approx(sonnet)


def test_paid_profile_builds_without_network():
    p = build_providers(Settings(_env_file=None, provider_profile="paid"))
    assert isinstance(p.chat, AnthropicText) and p.chat.model != p.report.model
    assert all(x.is_paid for x in (p.chat, p.report, p.stt, p.tts))
