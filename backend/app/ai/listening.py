import json
import re
import sqlite3
from datetime import timezone

from app.ai.prompts import render
from app.ai.schemas import ListeningSet
from app.ai.structured import generate_structured
from app.audio import save_audio
from app.db import insert
from app.deps import AppDeps
from app.errors import InvalidAIOutput
from app.providers.base import Msg

LESSON_ITEMS = 5


def _recent_mistakes(conn: sqlite3.Connection, module_id: str, limit: int = 5) -> str:
    rows = conn.execute(
        "SELECT said, corrected FROM mistakes WHERE module_id = ? ORDER BY id DESC LIMIT ?",
        (module_id, limit),
    ).fetchall()
    if not rows:
        return "(none yet)"
    return "\n".join(f'- said "{r["said"]}" -> should be "{r["corrected"]}"' for r in rows)


def _build_items(deps: AppDeps, module_id: str, count: int, personal: bool) -> list[dict]:
    """Ask the AI for `count` exercises and record their audio. Nothing is saved to the database here."""
    module = deps.content.get(module_id)
    choice_count, gap_count = (3, 2) if count == 5 else (2, 1)
    system = render(
        "listening", deps.settings.prompts_dir,
        level=module.level, module_title=module.title,
        target_structures=", ".join(module.target_structures),
        recent_mistakes=_recent_mistakes(deps.conn, module_id) if personal else "(none yet)",
        count=count, choice_count=choice_count, gap_count=gap_count,
    )
    result = generate_structured(
        deps.providers.report, system, [Msg("user", "Create the exercises now.")], ListeningSet, deps.tracker)
    if len(result.items) != count:
        raise InvalidAIOutput()

    items = []
    for item in result.items:
        deps.tracker.ensure_can_spend(deps.providers.tts.is_paid)
        speech = deps.providers.tts.synthesize(item.audio_text)
        deps.tracker.record(speech.usage)
        items.append({
            "kind": item.kind, "prompt": item.prompt, "audio_text": item.audio_text,
            "audio_path": save_audio(deps.settings.data_dir, speech.audio, speech.mime),
            "options": item.options, "answer": item.answer, "explanation": item.explanation,
        })
    return items


def _attach(deps: AppDeps, session_id: int, items: list[dict]) -> None:
    for item in items:
        insert(
            deps.conn, "listening_items",
            session_id=session_id, kind=item["kind"], prompt=item["prompt"], audio_text=item["audio_text"],
            audio_path=item["audio_path"], options=json.dumps(item["options"]) if item["options"] else None,
            answer=item["answer"], explanation=item["explanation"],
        )


def load_bank(conn: sqlite3.Connection, module_id: str) -> list[dict] | None:
    """The saved lesson exercises of a module (made once, like a book), or None if not made yet."""
    row = conn.execute("SELECT items FROM lesson_bank WHERE module_id = ?", (module_id,)).fetchone()
    return json.loads(row["items"]) if row else None


def ensure_lesson_bank(deps: AppDeps, module_id: str) -> bool:
    """Make and save the lesson exercises of a module if they do not exist yet. True if it had to make them."""
    if load_bank(deps.conn, module_id) is not None:
        return False
    items = _build_items(deps, module_id, LESSON_ITEMS, personal=False)  # generic: shared by every attempt
    deps.conn.execute(
        "INSERT OR IGNORE INTO lesson_bank (module_id, items, created_at) VALUES (?, ?, ?)",
        (module_id, json.dumps(items), deps.clock.now().astimezone(timezone.utc).isoformat()),
    )
    deps.conn.commit()
    return True


def generate_listening(deps: AppDeps, session_id: int, module_id: str, count: int = 5, from_bank: bool = False) -> None:
    """Give a session its exercises.

    Lessons (`from_bank`) reuse the saved set, so only the first opening of a module uses the AI.
    Reviews get fresh exercises built around the learner's recent mistakes.
    """
    if from_bank:
        ensure_lesson_bank(deps, module_id)
        _attach(deps, session_id, load_bank(deps.conn, module_id))
    else:
        _attach(deps, session_id, _build_items(deps, module_id, count, personal=True))


def list_items(conn: sqlite3.Connection, session_id: int) -> list[dict]:
    rows = conn.execute("SELECT * FROM listening_items WHERE session_id = ? ORDER BY id", (session_id,)).fetchall()
    return [
        {
            "id": r["id"], "kind": r["kind"], "prompt": r["prompt"],
            "options": json.loads(r["options"]) if r["options"] else None,
            "audio_url": f"/audio/{r['audio_path']}",
        }
        for r in rows
    ]


def _normalize(text: str) -> str:
    return " ".join(re.sub(r"[^\w\s']", "", text.lower()).split())


def is_correct(expected: str, given: str) -> bool:
    return _normalize(expected) == _normalize(given)
