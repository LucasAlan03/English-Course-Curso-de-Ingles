import io

from app.providers.base import SttResult, Usage

NO_SPEECH_THRESHOLD = 0.6
SAMPLE_RATE = 16000


def pick_language(probabilities) -> str:
    """Portuguese or English, whichever the model finds more likely (English when unsure)."""
    table = dict(probabilities or [])
    return "pt" if table.get("pt", 0.0) > table.get("en", 0.0) else "en"


def _decode(source):
    from faster_whisper.audio import decode_audio  # heavy import, only when used

    return decode_audio(source, sampling_rate=SAMPLE_RATE)


class LocalWhisperStt:
    """Speech-to-text with faster-whisper running on this PC (no API cost).

    The learner may speak English or Portuguese; the transcript keeps the language that was spoken.
    """

    is_paid = False

    def __init__(self, model_size: str = "small", model=None, decode=None):
        self.model_size = model_size
        self._model = model
        self._decode = decode or _decode

    def _get_model(self):
        if self._model is None:
            from faster_whisper import WhisperModel  # heavy import, only when used

            self._model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
        return self._model

    def transcribe(self, audio: bytes, mime: str) -> SttResult:
        model = self._get_model()
        samples = self._decode(io.BytesIO(audio))
        _, _, probabilities = model.detect_language(samples)
        language = pick_language(probabilities)
        segments, info = model.transcribe(samples, language=language, vad_filter=True)
        # Whisper invents phrases such as "Thank you." from noise; keep only segments it believes are speech.
        text = " ".join(
            s.text.strip() for s in segments if getattr(s, "no_speech_prob", 0.0) < NO_SPEECH_THRESHOLD
        ).strip()
        return SttResult(text, Usage("local", "faster-whisper", "stt", int(round(info.duration)), 0))
