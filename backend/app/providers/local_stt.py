import io
import os

from app.providers.base import SttResult, Usage

NO_SPEECH_THRESHOLD = 0.6
SAMPLE_RATE = 16000
SUPPORTED = ("en", "pt")


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

    def __init__(self, model_size: str = "small", model=None, decode=None, cpu_threads: int = 0):
        self.model_size = model_size
        self._model = model
        self._decode = decode or _decode
        self._cpu_threads = cpu_threads or max(4, (os.cpu_count() or 8) // 2)

    def _get_model(self):
        if self._model is None:
            from faster_whisper import WhisperModel  # heavy import, only when used

            self._model = WhisperModel(
                self.model_size, device="cpu", compute_type="int8", cpu_threads=self._cpu_threads
            )
        return self._model

    def warm_up(self) -> None:
        """Load the model now so the first real request does not pay for it."""
        self._get_model()

    def _run(self, model, samples, language):
        # Greedy decoding and no cross-segment conditioning are much faster and fine for short phrases.
        return model.transcribe(
            samples, language=language, vad_filter=True, beam_size=1, condition_on_previous_text=False
        )

    def transcribe(self, audio: bytes, mime: str) -> SttResult:
        model = self._get_model()
        samples = self._decode(io.BytesIO(audio))
        segments, info = self._run(model, samples, None)  # detects the language in the same pass
        if info.language not in SUPPORTED:
            segments, info = self._run(model, samples, pick_language(getattr(info, "all_language_probs", None)))
        # Whisper invents phrases such as "Thank you." from noise; keep only segments it believes are speech.
        text = " ".join(
            s.text.strip() for s in segments if getattr(s, "no_speech_prob", 0.0) < NO_SPEECH_THRESHOLD
        ).strip()
        return SttResult(text, Usage("local", "faster-whisper", "stt", int(round(info.duration)), 0))
