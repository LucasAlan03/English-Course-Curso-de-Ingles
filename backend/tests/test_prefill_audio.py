from app.content import Exercise
from app.reviews import ensure_exercise_audio, exercise_audio_name
from builders import valid_exercises


class CountingTts:
    is_paid = False

    def __init__(self, inner):
        self.inner, self.calls = inner, 0

    def synthesize(self, text):
        self.calls += 1
        return self.inner.synthesize(text)


def test_audio_is_synthesized_once(deps):
    tts = CountingTts(deps.providers.tts)
    deps.providers.tts = tts
    exercise = Exercise(**next(e for e in valid_exercises() if e["type"] == "dictation"))
    name = ensure_exercise_audio(deps, "b1_x", exercise)
    assert name == exercise_audio_name("b1_x", exercise.id) == f"ex_b1_x_{exercise.id}.wav"
    ensure_exercise_audio(deps, "b1_x", exercise)
    assert tts.calls == 1
    assert (deps.settings.data_dir and name)
