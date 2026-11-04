import io

from app.providers.base import SttResult, Usage


class LocalWhisperStt:
    """Speech-to-text with faster-whisper running on this PC (no API cost)."""

    is_paid = False

    def __init__(self, model_size: str = "base", model=None):
        self.model_size = model_size
        self._model = model

    def _get_model(self):
        if self._model is None:
            from faster_whisper import WhisperModel  # heavy import, only when used

            self._model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
        return self._model

    def transcribe(self, audio: bytes, mime: str) -> SttResult:
        segments, info = self._get_model().transcribe(io.BytesIO(audio), language="en")
        text = " ".join(s.text.strip() for s in segments).strip()
        return SttResult(text, Usage("local", "faster-whisper", "stt", int(round(info.duration)), 0))
