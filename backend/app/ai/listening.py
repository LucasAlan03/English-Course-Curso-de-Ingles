import json
import re
import sqlite3

from app.ai.prompts import render
from app.ai.schemas import ListeningSet
from app.ai.structured import generate_structured
from app.audio import save_audio
from app.db import insert
from app.deps import AppDeps
from app.errors import InvalidAIOutput
from app.providers.base import Msg


def _recent_mistakes(conn: sqlite3.Connection, module_id: str, limit: int = 5) -> str:
    rows = conn.execute(
        "SELECT said, corrected FROM mistakes WHERE module_id = ? ORDER BY id DESC LIMIT ?",
        (module_id, limit),
    ).fetchall()
    if not rows:
        return "(none yet)"
    return "\n".join(f'- said "{r["said"]}" -> should be "{r["corrected"]}"' for r in rows)


def generate_listening(deps: AppDeps, session_id: int, module_id: str, count: int = 5) -> None:
    """Generate `count` exercises with audio for a session and save them.

    Nothing is written to the database unless the AI output is valid and every audio clip exists.
    """
    module = deps.content.get(module_id)
    choice_count, gap_count = (3, 2) if count == 5 else (2, 1)
    system = render(
        "listening", deps.settings.prompts_dir,
        level=module.level, module_title=module.title,
        target_structures=", ".join(module.target_structures),
        recent_mistakes=_recent_mistakes(deps.conn, module_id),
        count=count, choice_count=choice_count, gap_count=gap_count,
    )
    result = generate_structured(
        deps.providers.report, system, [Msg("user", "Create the exercises now.")], ListeningSet, deps.tracker)
    if len(result.items) != count:
        raise InvalidAIOutput()

    clips = []
    for item in result.items:
        deps.tracker.ensure_can_spend(deps.providers.tts.is_paid)
        speech = deps.providers.tts.synthesize(item.audio_text)
        deps.tracker.record(speech.usage)
        clips.append(save_audio(deps.settings.data_dir, speech.audio, speech.mime))

    for item, clip in zip(result.items, clips):
        insert(
            deps.conn, "listening_items",
            session_id=session_id, kind=item.kind, prompt=item.prompt, audio_text=item.audio_text,
            audio_path=clip, options=json.dumps(item.options) if item.options else None,
            answer=item.answer, explanation=item.explanation,
        )


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
