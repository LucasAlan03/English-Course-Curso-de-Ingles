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
    def __init__(self, texts=("Hello", " there"), duration=2.4, no_speech=None):
        self._texts, self._duration, self.calls = texts, duration, []
        self._no_speech = no_speech or [0.0] * len(texts)

    def transcribe(self, audio, language=None, **kwargs):
        self.calls.append({"language": language, **kwargs})
        segments = [SimpleNamespace(text=t, no_speech_prob=p) for t, p in zip(self._texts, self._no_speech)]
        return iter(segments), SimpleNamespace(duration=self._duration)


class FakePiperVoice:
    def synthesize_wav(self, text, wav_file: wave.Wave_write, **kwargs):
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(22050)
        wav_file.writeframes(b"\x00\x00" * 100)


class BillingError(Exception):
    status_code = 402


class InsufficientQuota(Exception):
    status_code = 429


class PlainRateLimit(Exception):
    status_code = 429


class FakeAnthropicClient:
    def __init__(self, text="hi from claude", errors=None, stop_reason="end_turn"):
        self.messages = self
        self.calls = []
        self.errors = list(errors or [])
        self._text, self._stop = text, stop_reason

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.errors:
            raise self.errors.pop(0)
        content = [SimpleNamespace(type="thinking", thinking=""), SimpleNamespace(type="text", text=self._text)]
        return SimpleNamespace(content=content, stop_reason=self._stop,
                               usage=SimpleNamespace(input_tokens=12, output_tokens=7))


class FakeOpenAIClient:
    def __init__(self, transcript="hello", audio=b"RIFFfake", errors=None):
        self.audio = SimpleNamespace(
            transcriptions=SimpleNamespace(create=self._transcribe),
            speech=SimpleNamespace(create=self._speak),
        )
        self.calls = []
        self.errors = list(errors or [])
        self._transcript, self._audio = transcript, audio

    def _maybe_fail(self):
        if self.errors:
            raise self.errors.pop(0)

    def _transcribe(self, **kwargs):
        self.calls.append(("stt", kwargs))
        self._maybe_fail()
        return SimpleNamespace(text=self._transcript)

    def _speak(self, **kwargs):
        self.calls.append(("tts", kwargs))
        self._maybe_fail()
        return SimpleNamespace(content=self._audio)


class ServerError(Exception):
    code = 503


class AuthError(Exception):
    status_code = 401
