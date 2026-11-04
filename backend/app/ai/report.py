import json
import sqlite3
from datetime import date, datetime, timezone

from app.ai.conversation import transcript
from app.ai.prompts import render
from app.ai.schemas import Report
from app.ai.structured import generate_structured
from app.deps import AppDeps
from app.errors import AppError
from app.mistakes import record_mistakes
from app.providers.base import Msg
from app.scoring import final_score
from app.sessions_repo import get_session
from app.srs import ReviewState, next_state


def _listening_pct(conn: sqlite3.Connection, session_id: int) -> float | None:
    rows = conn.execute("SELECT correct FROM listening_items WHERE session_id = ?", (session_id,)).fetchall()
    if not rows:
        return None
    return 100 * sum(1 for r in rows if r["correct"]) / len(rows)  # unanswered counts as wrong


def _schedule_review(deps: AppDeps, module_id: str, score: int, today: date) -> str:
    row = deps.conn.execute("SELECT * FROM reviews WHERE module_id = ?", (module_id,)).fetchone()
    prev = ReviewState(row["interval_days"], row["ease"], row["repetitions"],
                       date.fromisoformat(row["next_due"])) if row else None
    state = next_state(prev, score, today)
    deps.conn.execute(
        "INSERT OR REPLACE INTO reviews (module_id, next_due, interval_days, ease, repetitions, last_score) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (module_id, state.next_due.isoformat(), state.interval_days, state.ease, state.repetitions, score),
    )
    deps.conn.commit()
    return state.next_due.isoformat()


def finish_session(deps: AppDeps, session: sqlite3.Row) -> dict:
    """Write the report, score the session and schedule the next review. Safe to call twice."""
    if session["is_finished"] and session["report_json"]:
        return json.loads(session["report_json"])
    if session["kind"] not in ("lesson", "review", "free"):
        raise AppError("invalid_session_kind", 400, "Esta sessão não gera relatório de conversa.")

    session_id = session["id"]
    rows = deps.conn.execute("SELECT role, text FROM messages WHERE session_id = ? ORDER BY id", (session_id,)).fetchall()
    messages = [Msg(r["role"], r["text"]) for r in rows]
    if not any(m.role == "user" for m in messages):
        raise AppError("no_user_messages", 422, "Fale ou escreva algo antes de encerrar.")

    claimed = deps.conn.execute(
        "UPDATE sessions SET is_finished = 2 WHERE id = ? AND is_finished = 0", (session_id,)
    ).rowcount
    deps.conn.commit()
    if not claimed:  # another request is finishing it, or already did
        fresh = get_session(deps.conn, session_id)
        if fresh["is_finished"] == 1 and fresh["report_json"]:
            return json.loads(fresh["report_json"])
        raise AppError("finish_in_progress", 409, "O relatório já está sendo gerado. Aguarde alguns segundos.")
    try:
        return _finish_claimed(deps, session, messages)
    except BaseException:
        deps.conn.execute("UPDATE sessions SET is_finished = 0 WHERE id = ? AND is_finished = 2", (session_id,))
        deps.conn.commit()
        raise


def _finish_claimed(deps: AppDeps, session: sqlite3.Row, messages: list[Msg]) -> dict:
    session_id = session["id"]
    if session["kind"] == "free":
        level = deps.settings.user_level
        context = f"Free conversation about: {session['topic'] or 'anything'}"
    else:
        module = deps.content.get(session["module_id"])
        level = module.level
        context = f"{module.title}. Goal: {module.scenario.goal}. Target structures: {', '.join(module.target_structures)}"
    system = render("report", deps.settings.prompts_dir, level=level, module_context=context,
                    known_module_ids=", ".join(deps.content.ids()), transcript=transcript(messages))
    report = generate_structured(deps.providers.report, system, [Msg("user", "Write the report now.")],
                                 Report, deps.tracker)

    now = deps.clock.now().astimezone(timezone.utc)
    today = deps.clock.today()
    listening = _listening_pct(deps.conn, session_id)
    listening_score = round(listening) if listening is not None else None
    final = final_score(listening, report.score)

    next_due = None
    if session["kind"] in ("lesson", "review"):
        next_due = _schedule_review(deps, session["module_id"], final, today)
    record_mistakes(deps, session_id, report.mistakes, session["module_id"])

    result = {"report": report.model_dump(), "listening_score": listening_score,
              "conversation_score": report.score, "final_score": final, "next_due": next_due}
    duration = int((now - datetime.fromisoformat(session["started_at"])).total_seconds())
    deps.conn.execute(
        "UPDATE sessions SET listening_score = ?, conversation_score = ?, final_score = ?, finished_at = ?, "
        "day = ?, duration_s = ?, is_finished = 1, report_json = ? WHERE id = ?",
        (listening_score, report.score, final, now.isoformat(), today.isoformat(), max(duration, 0),
         json.dumps(result), session_id),
    )
    deps.conn.commit()
    return result
