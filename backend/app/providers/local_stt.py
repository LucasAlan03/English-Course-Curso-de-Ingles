import io

from app.providers.base import SttResult, Usage


NO_SPEECH_THRESHOLD = 0.6


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
        segments, info = self._get_model().transcribe(io.BytesIO(audio), language="en", vad_filter=True)
        # Whisper invents phrases such as "Thank you." from noise; keep only segments it believes are speech.
        text = " ".join(
            s.text.strip() for s in segments if getattr(s, "no_speech_prob", 0.0) < NO_SPEECH_THRESHOLD
        ).strip()
        return SttResult(text, Usage("local", "faster-whisper", "stt", int(round(info.duration)), 0))
