"""Makes the listening exercises of every lesson ahead of time, so opening a lesson is instant and free.

    python scripts/prefill_lessons.py            # all modules that do not have exercises yet
    python scripts/prefill_lessons.py --only b1_futures

It is safe to stop and run again: modules that are already done are skipped. When the AI provider
answers "too many requests", the script waits and keeps going (the free Gemini plan has daily limits).
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ai.prefill import prefill_lesson_bank  # noqa: E402
from app.config import Settings  # noqa: E402
from app.main import create_app  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", help="make just this module")
    parser.add_argument("--wait", type=float, default=30, help="seconds to wait when the provider is busy")
    parser.add_argument("--max-waits", type=int, default=20)
    args = parser.parse_args()

    deps = create_app(Settings()).state.deps
    ids = [args.only] if args.only else deps.content.ids()
    result = prefill_lesson_bank(deps, ids, wait_s=args.wait, max_waits=args.max_waits)
    print(f"done: {len(result['done'])}  already there: {len(result['skipped'])}  failed: {len(result['failed'])}")
    if result["failed"]:
        print("Run the script again later to finish: " + ", ".join(result["failed"]))
    return 1 if result["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
