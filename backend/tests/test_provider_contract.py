import pytest

from app.providers.base import Msg, SttResult, TextResult, TtsResult, Usage
from app.providers.fakes import FakeStt, FakeTextModel, FakeTts
from app.providers.gemini import GeminiText
from app.providers.local_stt import LocalWhisperStt
from app.providers.local_tts import LocalTts
from app.providers.anthropic_provider import AnthropicText
from app.providers.openai_provider import OpenAIStt, OpenAITts
from sdk_fakes import (FakeAnthropicClient, FakeGeminiClient, FakeOpenAIClient, FakePiperVoice,
                       FakeWhisperModel)

# Real implementations are appended to these lists in the free/paid provider tasks.
TEXT_CASES = [
    lambda: FakeTextModel(["hello"]),
    lambda: GeminiText("k", "m", client=FakeGeminiClient("hello")),
    lambda: AnthropicText("k", "claude-haiku-5-5", client=FakeAnthropicClient("hello")),
]
STT_CASES = [
    lambda: FakeStt("hello"),
    lambda: LocalWhisperStt(model=FakeWhisperModel()),
    lambda: OpenAIStt("k", "m", client=FakeOpenAIClient("hello")),
]
TTS_CASES = [
    lambda: FakeTts(),
    lambda: LocalTts(voice=FakePiperVoice()),
    lambda: OpenAITts("k", "m", "alloy", client=FakeOpenAIClient()),
]


@pytest.mark.parametrize("make", TEXT_CASES)
def test_text_contract(make):
    model = make()
    result = model.generate("sys", [Msg("user", "hi")], json_mode=False)
    assert isinstance(result, TextResult) and isinstance(result.text, str) and result.text
    assert isinstance(result.usage, Usage) and result.usage.kind == "text"
    assert isinstance(model.is_paid, bool)


@pytest.mark.parametrize("make", STT_CASES)
def test_stt_contract(make):
    stt = make()
    result = stt.transcribe(b"audio-bytes", "audio/wav")
    assert isinstance(result, SttResult) and result.text
    assert result.usage.kind == "stt" and isinstance(stt.is_paid, bool)


@pytest.mark.parametrize("make", TTS_CASES)
def test_tts_contract(make):
    tts = make()
    result = tts.synthesize("hello there")
    assert isinstance(result, TtsResult) and isinstance(result.audio, bytes) and result.audio
    assert result.mime.startswith("audio/") and result.usage.kind == "tts"
    assert isinstance(tts.is_paid, bool)


def test_fake_text_model_records_calls_and_runs_out():
    fake = FakeTextModel(["a"])
    fake.generate("s", [Msg("user", "x")])
    assert fake.calls[0][0] == "s"
    with pytest.raises(AssertionError):
        fake.generate("s", [Msg("user", "x")])
