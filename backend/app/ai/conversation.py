import sqlite3
from datetime import timezone

from app.ai.prompts import render
from app.audio import save_audio
from app.db import insert
from app.deps import AppDeps
from app.errors import AppError, EmptyTranscript
from app.providers.base import Msg, TextModel
from app.usage import UsageTracker

RECENT_KEEP = 10  # messages that always travel verbatim
REFRESH_AT = 15  # unsummarized messages that trigger a new summary
OPENER = "(The learner is ready. Start the conversation in character with a short greeting and one question.)"


def persona_prompt(deps: AppDeps, session: sqlite3.Row) -> str:
    if session["kind"] == "free":
        topic = session["topic"] or "anything the learner likes"
        return render(
            "chat_persona", deps.settings.prompts_dir,
            level=deps.settings.user_level, scenario_title=f"Free conversation about {topic}",
            character="a friendly native English speaker", goal="Have a natural, enjoyable conversation",
            target_structures="none - just keep the conversation going",
        )
    module = deps.content.get(session["module_id"])
    return render(
        "chat_persona", deps.settings.prompts_dir,
        level=module.level, scenario_title=module.scenario.title, character=module.scenario.character,
        goal=module.scenario.goal, target_structures=", ".join(module.target_structures),
    )


def transcript(messages: list[Msg]) -> str:
    return "\n".join(f"{'LEARNER' if m.role == 'user' else 'AI'}: {m.content}" for m in messages)


def build_context(
    messages: list[Msg], summary: str | None, summary_upto: int, chat: TextModel, tracker: UsageTracker
) -> tuple[str | None, int, list[Msg]]:
    """Messages to send to the model: a rolling summary plus the recent messages verbatim.

    The summary is refreshed in batches, so most turns cost no extra summary call.
    """
    unsummarized = messages[summary_upto:]
    if len(unsummarized) < REFRESH_AT:
        return summary, summary_upto, unsummarized
    cut = len(messages) - RECENT_KEEP
    prompt = render(
        "summary", tracker.settings.prompts_dir,
        previous_summary=summary or "(none)", transcript=transcript(messages[summary_upto:cut]),
    )
    tracker.ensure_can_spend(chat.is_paid)
    result = chat.generate("You write short, faithful conversation notes.", [Msg("user", prompt)])
    tracker.record(result.usage)
    return result.text.strip(), cut, messages[cut:]


def _history(conn: sqlite3.Connection, session_id: int) -> list[Msg]:
    rows = conn.execute("SELECT role, text FROM messages WHERE session_id = ? ORDER BY id", (session_id,)).fetchall()
    return [Msg(r["role"], r["text"]) for r in rows]


def run_turn(deps: AppDeps, session: sqlite3.Row, text: str | None, audio: bytes | None,
             mime: str, want_audio: bool) -> dict:
    if session["is_finished"]:
        raise AppError("session_finished", 409, "Esta sessão já foi encerrada.")
    if session["kind"] not in ("lesson", "review", "free"):
        raise AppError("invalid_session_kind", 400, "Esta sessão não tem conversa.")
    providers, tracker, session_id = deps.providers, deps.tracker, session["id"]
    tracker.ensure_can_spend(providers.chat.is_paid)

    user_text = ""
    if audio is not None:
        tracker.ensure_can_spend(providers.stt.is_paid)
        heard = providers.stt.transcribe(audio, mime)
        tracker.record(heard.usage)
        user_text = heard.text.strip()
        if not user_text:
            raise EmptyTranscript()
    elif text is not None:
        user_text = text.strip()
        if not user_text:
            raise AppError("empty_message", 422, "Escreva ou fale alguma coisa.")

    history = _history(deps.conn, session_id)
    opener = audio is None and text is None
    if opener and history:
        raise AppError("empty_message", 422, "Escreva ou fale alguma coisa.")

    now = deps.clock.now().astimezone(timezone.utc).isoformat()
    summary, upto = session["summary"], session["summary_upto"]
    if opener:
        recent = [Msg("user", OPENER)]
    else:
        insert(deps.conn, "messages", session_id=session_id, role="user", text=user_text, created_at=now)
        history.append(Msg("user", user_text))
        new_summary, new_upto, recent = build_context(history, summary, upto, providers.chat, tracker)
        if new_upto != upto:
            deps.conn.execute("UPDATE sessions SET summary = ?, summary_upto = ? WHERE id = ?",
                              (new_summary, new_upto, session_id))
            deps.conn.commit()
        summary = new_summary

    system = persona_prompt(deps, session)
    if summary:
        system += f"\n\nSummary of the earlier part of this conversation:\n{summary}"
    reply = providers.chat.generate(system, recent)
    tracker.record(reply.usage)
    reply_text = reply.text.strip()

    audio_name = None
    if want_audio:
        tracker.ensure_can_spend(providers.tts.is_paid)
        speech = providers.tts.synthesize(reply_text)
        tracker.record(speech.usage)
        audio_name = save_audio(deps.settings.data_dir, speech.audio, speech.mime)
    insert(deps.conn, "messages", session_id=session_id, role="assistant", text=reply_text,
           audio_path=audio_name, created_at=now)
    return {"user_text": user_text, "reply_text": reply_text,
            "reply_audio_url": f"/audio/{audio_name}" if audio_name else None}
