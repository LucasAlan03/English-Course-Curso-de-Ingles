import io
import os
import wave

from app.providers.base import TtsResult, Usage


class LocalTts:
    """Text-to-speech with a Piper voice running on this PC (no API cost)."""

    is_paid = False

    def __init__(self, voice_path: str = "", voice=None):
        self.voice_path = voice_path
        self._voice = voice

    def _get_voice(self):
        if self._voice is None:
            if not os.path.isfile(self.voice_path):
                raise RuntimeError(
                    f"Piper voice file not found: {self.voice_path}. See README for how to download it."
                )
            from piper import PiperVoice  # heavy import, only when used

            self._voice = PiperVoice.load(self.voice_path)
        return self._voice

    def synthesize(self, text: str) -> TtsResult:
        voice = self._get_voice()
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            voice.synthesize_wav(text, wav_file)
        return TtsResult(buffer.getvalue(), "audio/wav", Usage("local", "piper", "tts", len(text), 0))
