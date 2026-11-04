"""Stand-ins for third-party SDK objects, so provider adapters are tested without network or models."""
import wave
from types import SimpleNamespace


class QuotaError(Exception):
    code = 429


class FakeGeminiClient:
    def __init__(self, text="hi there", errors=None, prompt_tokens=10, output_tokens=5):
        self.models = self
        self.calls = []
        self.errors = list(errors or [])
        self._text = text
        self._usage = SimpleNamespace(prompt_token_count=prompt_tokens, candidates_token_count=output_tokens)

    def generate_content(self, model, contents, config):
        self.calls.append({"model": model, "contents": contents, "config": config})
        if self.errors:
            raise self.errors.pop(0)
        return SimpleNamespace(text=self._text, usage_metadata=self._usage)


class FakeWhisperModel:
    def __init__(self, texts=("Hello", " there"), duration=2.4):
        self._texts, self._duration, self.calls = texts, duration, []

    def transcribe(self, audio, language=None):
        self.calls.append(language)
        segments = [SimpleNamespace(text=t) for t in self._texts]
        return iter(segments), SimpleNamespace(duration=self._duration)


class FakePiperVoice:
    def synthesize_wav(self, text, wav_file: wave.Wave_write, **kwargs):
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(22050)
        wav_file.writeframes(b"\x00\x00" * 100)
