"""Records the audio of every listening and dictation exercise once (Piper, local and free).

    python scripts/prefill_audio.py                 # every module
    python scripts/prefill_audio.py --only b1_past_simple

Safe to stop and run again: audio files that already exist are skipped.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.audio import audio_dir  # noqa: E402
from app.config import Settings  # noqa: E402
from app.main import create_app  # noqa: E402
from app.reviews import ensure_exercise_audio, exercise_audio_name  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", help="record just this module")
    args = parser.parse_args()

    settings = Settings()
    settings.warm_up = False
    deps = create_app(settings).state.deps
    ids = [args.only] if args.only else deps.content.ids()
    done = skipped = failed = 0
    for module_id in ids:
        for exercise in deps.content.exercises(module_id):
            if not exercise.audio_text:
                continue
            if (audio_dir(settings.data_dir) / exercise_audio_name(module_id, exercise.id)).is_file():
                skipped += 1
                continue
            try:
                ensure_exercise_audio(deps, module_id, exercise)
                done += 1
            except Exception as exc:  # keep going; the next run retries
                failed += 1
                print(f"failed {module_id}/{exercise.id}: {exc}")
    print(f"done: {done}  skipped: {skipped}  failed: {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
