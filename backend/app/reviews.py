"""Spaced-repetition scheduling and pre-recorded exercise audio."""

from datetime import date

from app.audio import audio_dir
from app.deps import AppDeps
from app.srs import ReviewState, next_state


def schedule_review(deps: AppDeps, module_id: str, score: int) -> str:
    row = deps.conn.execute("SELECT * FROM reviews WHERE module_id = ?", (module_id,)).fetchone()
    prev = ReviewState(row["interval_days"], row["ease"], row["repetitions"],
                       date.fromisoformat(row["next_due"])) if row else None
    state = next_state(prev, score, deps.clock.today())
    deps.conn.execute(
        "INSERT OR REPLACE INTO reviews (module_id, next_due, interval_days, ease, repetitions, last_score) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (module_id, state.next_due.isoformat(), state.interval_days, state.ease, state.repetitions, score),
    )
    deps.conn.commit()
    return state.next_due.isoformat()


def exercise_audio_name(module_id: str, exercise_id: str) -> str:
    return f"ex_{module_id}_{exercise_id}.wav"


def ensure_exercise_audio(deps: AppDeps, module_id: str, exercise) -> str:
    """Synthesize the exercise audio once; later calls reuse the file."""
    name = exercise_audio_name(module_id, exercise.id)
    path = audio_dir(deps.settings.data_dir) / name
    if not path.is_file():
        deps.tracker.ensure_can_spend(deps.providers.tts.is_paid)
        speech = deps.providers.tts.synthesize(exercise.audio_text)
        deps.tracker.record(speech.usage)
        path.write_bytes(speech.audio)
    return name
