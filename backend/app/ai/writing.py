import json
from datetime import datetime, timezone

from app.ai.prompts import render
from app.ai.schemas import WritingFeedback
from app.ai.structured import generate_structured
from app.db import insert
from app.deps import AppDeps
from app.errors import AppError
from app.mistakes import record_mistakes
from app.providers.base import Msg
from app.sessions_repo import get_session

MIN_TEXT_CHARS = 10


def new_writing_prompt(deps: AppDeps) -> dict:
    recent = deps.conn.execute(
        "SELECT topic FROM sessions WHERE kind = 'writing' AND topic IS NOT NULL ORDER BY id DESC LIMIT 5"
    ).fetchall()
    system = render("writing_prompt", deps.settings.prompts_dir, level=deps.settings.user_level,
                    recent_topics="; ".join(r["topic"] for r in recent) or "(none)")
    deps.tracker.ensure_can_spend(deps.providers.chat.is_paid)
    result = deps.providers.chat.generate(system, [Msg("user", "Give me the topic.")])
    deps.tracker.record(result.usage)
    topic = result.text.strip().strip('"')
    session_id = insert(deps.conn, "sessions", kind="writing", topic=topic, started_at=deps.clock.now().isoformat())
    return {"session_id": session_id, "prompt": topic}


def submit_writing(deps: AppDeps, session_id: int, text: str) -> dict:
    session = get_session(deps.conn, session_id)
    if session["kind"] != "writing":
        raise AppError("invalid_session_kind", 400, "Esta sessão não é de escrita.")
    if session["is_finished"]:
        raise AppError("session_finished", 409, "Este texto já foi corrigido.")
    text = text.strip()
    if len(text) < MIN_TEXT_CHARS:
        raise AppError("text_too_short", 422, "Escreva um pouco mais para eu poder corrigir.")

    system = render("writing_feedback", deps.settings.prompts_dir, level=deps.settings.user_level,
                    prompt=session["topic"], known_module_ids=", ".join(deps.content.ids()), text=text)
    feedback = generate_structured(deps.providers.report, system, [Msg("user", "Correct the text now.")],
                                   WritingFeedback, deps.tracker)

    now = deps.clock.now().astimezone(timezone.utc)
    insert(deps.conn, "messages", session_id=session_id, role="user", text=text, created_at=now.isoformat())
    record_mistakes(deps, session_id, feedback.mistakes, None)
    duration = max(int((now - datetime.fromisoformat(session["started_at"])).total_seconds()), 0)
    result = feedback.model_dump()
    deps.conn.execute(
        "UPDATE sessions SET conversation_score = ?, final_score = ?, finished_at = ?, day = ?, duration_s = ?, "
        "is_finished = 1, report_json = ? WHERE id = ?",
        (feedback.score, feedback.score, now.isoformat(), deps.clock.today().isoformat(), duration,
         json.dumps(result), session_id),
    )
    deps.conn.commit()
    return result
