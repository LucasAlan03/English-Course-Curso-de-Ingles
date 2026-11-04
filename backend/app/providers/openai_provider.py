from app.providers.base import SttResult, TtsResult, Usage
from app.providers.errors_map import classify

# The transcription response has no duration, so seconds are estimated from the size
# (about 12 KB per second for compressed phone/browser audio). Used only for the cost estimate.
_BYTES_PER_SECOND = 12_000


def _client(api_key: str):
    from openai import OpenAI  # imported lazily: only needed when actually used

    return OpenAI(api_key=api_key)


def _call(provider_call):
    try:
        return provider_call()
    except Exception as exc:
        mapped = classify(exc, "openai")
        if mapped:
            raise mapped from exc
        raise


class OpenAIStt:
    is_paid = True

    def __init__(self, api_key: str, model: str, client=None):
        self.api_key = api_key
        self.model = model
        self._client = client

    def transcribe(self, audio: bytes, mime: str) -> SttResult:
        client = self._client or _client(self.api_key)
        extension = mime.split("/")[-1].split(";")[0] or "wav"
        response = _call(lambda: client.audio.transcriptions.create(
            model=self.model, file=(f"audio.{extension}", audio, mime)))
        seconds = max(1, round(len(audio) / _BYTES_PER_SECOND))
        return SttResult(response.text, Usage("openai", self.model, "stt", seconds, 0))


class OpenAITts:
    is_paid = True

    def __init__(self, api_key: str, model: str, voice: str = "alloy", client=None):
        self.api_key = api_key
        self.model = model
        self.voice = voice
        self._client = client

    def synthesize(self, text: str) -> TtsResult:
        client = self._client or _client(self.api_key)
        response = _call(lambda: client.audio.speech.create(
            model=self.model, voice=self.voice, input=text, response_format="wav"))
        return TtsResult(response.content, "audio/wav", Usage("openai", self.model, "tts", len(text), 0))
