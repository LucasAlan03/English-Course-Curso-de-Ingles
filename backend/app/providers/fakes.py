from app.providers.base import Msg, SttResult, TextResult, TtsResult, Usage


class FakeTextModel:
    is_paid = False

    def __init__(self, responses: list[str] | None = None):
        self.responses = list(responses or [])
        self.calls: list[tuple[str, list[Msg], bool]] = []

    def generate(self, system: str, messages: list[Msg], json_mode: bool = False) -> TextResult:
        self.calls.append((system, list(messages), json_mode))
        assert self.responses, "FakeTextModel ran out of queued responses"
        text = self.responses.pop(0)
        return TextResult(text, Usage("fake", "fake-text", "text", len(system), len(text)))


class FakeStt:
    is_paid = False

    def __init__(self, text: str = "hello there"):
        self.text = text

    def transcribe(self, audio: bytes, mime: str) -> SttResult:
        return SttResult(self.text, Usage("fake", "fake-stt", "stt", 1, 0))


class FakeTts:
    is_paid = False

    def synthesize(self, text: str) -> TtsResult:
        return TtsResult(b"FAKEAUDIO", "audio/wav", Usage("fake", "fake-tts", "tts", len(text), 0))
