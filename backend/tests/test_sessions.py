import json
import os
from datetime import date

import pytest

from app.ai.conversation import build_context
from app.db import insert
from app.goals import pillars_for_day
from app.providers.base import Msg
from app.providers.fakes import FakeTextModel
from builders import add_user_message, make_session, report_json

MODULE = "b1_past_simple_continuous"


def count(deps, table, where="1=1"):
    return deps.conn.execute(f"SELECT COUNT(*) FROM {table} WHERE {where}").fetchone()[0]


def turn(app_client, sid, text=None, want_audio=False, audio=None):
    data = {"want_audio": str(want_audio).lower()}
    if text is not None:
        data["text"] = text
    files = {"audio": ("clip.webm", audio, "audio/webm")} if audio is not None else None
    return app_client.post(f"/sessions/{sid}/turn", data=data, files=files)


# ---------- creating sessions ----------

def test_create_lesson_session(app_client):
    r = app_client.post("/sessions", json={"kind": "lesson", "module_id": MODULE})
    assert r.status_code == 200 and isinstance(r.json()["id"], int)


def test_create_session_validation(app_client):
    assert app_client.post("/sessions", json={"kind": "lesson", "module_id": "nope"}).status_code == 404
    assert app_client.post("/sessions", json={"kind": "lesson"}).status_code == 422
    assert app_client.post("/sessions", json={"kind": "dance"}).status_code == 422
    assert app_client.post("/sessions", json={"kind": "free", "topic": "football"}).status_code == 200


# ---------- turns ----------

def test_turn_with_text_returns_reply_and_stores_messages(app_client, deps, providers):
    providers.chat.responses.append("Nice! Where did you go?")
    sid = make_session(deps)
    r = turn(app_client, sid, text="I went to the park yesterday.")
    assert r.status_code == 200
    assert r.json() == {"user_text": "I went to the park yesterday.",
                        "reply_text": "Nice! Where did you go?", "reply_audio_url": None}
    rows = deps.conn.execute("SELECT role, text FROM messages ORDER BY id").fetchall()
    assert [(x["role"], x["text"]) for x in rows] == [
        ("user", "I went to the park yesterday."), ("assistant", "Nice! Where did you go?")]
    system = providers.chat.calls[0][0]
    assert "friendly barista" in system and "Order a coffee" in system and "past simple" in system


def test_first_turn_without_input_makes_the_ai_open(app_client, deps, providers):
    providers.chat.responses.append("Hi there! What can I get you?")
    sid = make_session(deps)
    r = turn(app_client, sid)
    assert r.status_code == 200 and r.json()["user_text"] == ""
    assert r.json()["reply_text"] == "Hi there! What can I get you?"
    assert count(deps, "messages", "role = 'user'") == 0


def test_blank_text_later_is_rejected(app_client, deps, providers):
    sid = make_session(deps)
    add_user_message(deps, sid)
    r = turn(app_client, sid, text="   ")
    assert r.status_code == 422 and r.json()["error"] == "empty_message"
    assert providers.chat.calls == []


def test_turn_with_audio_transcribes_first(app_client, deps, providers):
    providers.stt.text = "I was reading when you called."
    providers.chat.responses.append("Oh really?")
    sid = make_session(deps)
    r = turn(app_client, sid, audio=b"fake-audio-bytes")
    assert r.status_code == 200 and r.json()["user_text"] == "I was reading when you called."


def test_empty_transcript_returns_422_and_no_ai_call(app_client, deps, providers):
    providers.stt.text = "   "
    sid = make_session(deps)
    r = turn(app_client, sid, audio=b"silence")
    assert r.status_code == 422 and r.json()["error"] == "empty_transcript"
    assert providers.chat.calls == [] and count(deps, "messages") == 0


def test_want_audio_returns_a_playable_url(app_client, deps, providers):
    providers.chat.responses.extend(["Hello!", "Great!"])
    sid = make_session(deps)
    without = turn(app_client, sid, text="Hi", want_audio=False).json()
    assert without["reply_audio_url"] is None
    with_audio = turn(app_client, sid, text="Hi again", want_audio=True).json()
    assert app_client.get(with_audio["reply_audio_url"]).content == b"FAKEAUDIO"


def test_turn_on_finished_session_is_409(app_client, deps):
    sid = make_session(deps, is_finished=1)
    assert turn(app_client, sid, text="hi").status_code == 409


def test_paid_provider_blocked_when_cap_reached(app_client, deps, providers):
    providers.chat.is_paid = True
    insert(deps.conn, "api_usage", provider="anthropic", model="m", kind="text", input_units=1,
           output_units=1, cost_brl=50.0, created_at=deps.clock.now().isoformat())
    sid = make_session(deps)
    r = turn(app_client, sid, text="Hi")
    assert r.status_code == 402 and r.json()["error"] == "monthly_cap_reached"


# ---------- conversation memory ----------

def msgs(n):
    return [Msg("user" if i % 2 == 0 else "assistant", f"m{i}") for i in range(n)]


def test_context_short_conversations_are_untouched(tracker):
    chat = FakeTextModel()
    summary, upto, recent = build_context(msgs(12), None, 0, chat, tracker)
    assert (summary, upto, len(recent)) == (None, 0, 12) and chat.calls == []


def test_context_keeps_last_10_and_summarizes_older(tracker):
    chat = FakeTextModel(["SUMMARY ONE"])
    summary, upto, recent = build_context(msgs(25), None, 0, chat, tracker)
    assert summary == "SUMMARY ONE" and upto == 15
    assert [m.content for m in recent] == [f"m{i}" for i in range(15, 25)]
    assert "m0" in chat.calls[0][1][0].content  # the old messages went into the summary request


def test_context_does_not_resummarize_every_turn(tracker):
    chat = FakeTextModel()
    summary, upto, recent = build_context(msgs(26), "SUMMARY ONE", 15, chat, tracker)
    assert (summary, upto, len(recent)) == ("SUMMARY ONE", 15, 11) and chat.calls == []


def test_turn_summarizes_long_history_and_uses_it(app_client, deps, providers):
    sid = make_session(deps)
    for i in range(30):
        insert(deps.conn, "messages", session_id=sid, role="user" if i % 2 == 0 else "assistant",
               text=f"old message {i}", created_at="x")
    providers.chat.responses.extend(["THE SUMMARY", "Fine, go on."])
    assert turn(app_client, sid, text="And then?").status_code == 200
    row = deps.conn.execute("SELECT summary, summary_upto FROM sessions WHERE id = ?", (sid,)).fetchone()
    assert row["summary"] == "THE SUMMARY" and row["summary_upto"] > 0
    assert "THE SUMMARY" in providers.chat.calls[-1][0]


# ---------- finishing ----------

def finished_lesson(app_client, deps, providers, score=90, mistakes=None):
    sid = make_session(deps)
    add_user_message(deps, sid)
    add_user_message(deps, sid, "She was cooking when I arrived.")
    providers.report.responses.append(report_json(score, mistakes))
    return sid, app_client.post(f"/sessions/{sid}/finish")


def test_finish_returns_scores_and_records_mistakes(app_client, deps, providers):
    mistakes = [{"said": "I goed", "corrected": "I went", "explanation": "irregular", "module_id": "b2_passive_voice"}]
    sid, r = finished_lesson(app_client, deps, providers, mistakes=mistakes)
    body = r.json()
    assert r.status_code == 200
    assert (body["conversation_score"], body["final_score"]) == (90, 90)
    assert body["next_due"] is None and body["report"]["score"] == 90 and count(deps, "reviews") == 0
    saved = deps.conn.execute("SELECT module_id, said FROM mistakes").fetchall()
    assert [(x["module_id"], x["said"]) for x in saved] == [(MODULE, "I goed")]  # session module wins
    assert pillars_for_day(deps.conn, date(2026, 11, 3))["grammar"] is True


def test_finish_twice_is_idempotent(app_client, deps, providers):
    sid, first = finished_lesson(app_client, deps, providers)
    again = app_client.post(f"/sessions/{sid}/finish")
    assert again.status_code == 200 and again.json() == first.json()
    assert count(deps, "reviews") == 0 and len(providers.report.calls) == 1


def test_finish_without_user_messages_changes_nothing(app_client, deps, providers):
    sid = make_session(deps)
    r = app_client.post(f"/sessions/{sid}/finish")
    assert r.status_code == 422 and r.json()["error"] == "no_user_messages"
    assert count(deps, "reviews") == 0 and providers.report.calls == []
    assert deps.conn.execute("SELECT is_finished FROM sessions WHERE id = ?", (sid,)).fetchone()[0] == 0


def test_finish_with_invalid_report_saves_nothing(app_client, deps, providers):
    sid = make_session(deps)
    add_user_message(deps, sid)
    providers.report.responses.extend(["bad", "bad again"])
    r = app_client.post(f"/sessions/{sid}/finish")
    assert r.status_code == 502 and count(deps, "reviews") == 0 and count(deps, "mistakes") == 0


def test_finish_writing_session_is_rejected(app_client, deps):
    sid = make_session(deps, kind="writing", module_id=None)
    assert app_client.post(f"/sessions/{sid}/finish").status_code == 400


def test_free_session_pulls_review_forward_after_3_mistakes(app_client, deps, providers):
    insert(deps.conn, "reviews", module_id="b1_futures", next_due="2026-12-01", interval_days=20, ease=2.5, repetitions=3)
    old = make_session(deps)
    for _ in range(2):
        insert(deps.conn, "mistakes", session_id=old, module_id="b1_futures", said="x", corrected="y",
               explanation="z", created_at=deps.clock.now().isoformat())
    sid = make_session(deps, kind="free", module_id=None, topic="travel")
    add_user_message(deps, sid)
    providers.report.responses.append(report_json(70, [
        {"said": "I will to go", "corrected": "I will go", "explanation": "e", "module_id": "b1_futures"},
        {"said": "weird", "corrected": "fine", "explanation": "e", "module_id": "not_a_module"},
    ]))
    assert app_client.post(f"/sessions/{sid}/finish").status_code == 200
    due = deps.conn.execute("SELECT next_due FROM reviews WHERE module_id = 'b1_futures'").fetchone()[0]
    assert due == "2026-11-04"
    unknown = deps.conn.execute("SELECT module_id FROM mistakes WHERE said = 'weird'").fetchone()
    assert unknown["module_id"] is None
    assert count(deps, "reviews") == 1  # a free chat never creates a review row


def test_old_mistakes_do_not_trigger_pull_forward(app_client, deps, providers):
    insert(deps.conn, "reviews", module_id="b1_futures", next_due="2026-12-01", interval_days=20, ease=2.5, repetitions=3)
    old = make_session(deps)
    for _ in range(2):
        insert(deps.conn, "mistakes", session_id=old, module_id="b1_futures", said="x", corrected="y",
               explanation="z", created_at="2026-10-01T10:00:00+00:00")
    sid = make_session(deps, kind="free", module_id=None)
    add_user_message(deps, sid)
    providers.report.responses.append(report_json(70, [
        {"said": "a", "corrected": "b", "explanation": "e", "module_id": "b1_futures"}]))
    app_client.post(f"/sessions/{sid}/finish")
    due = deps.conn.execute("SELECT next_due FROM reviews WHERE module_id = 'b1_futures'").fetchone()[0]
    assert due == "2026-12-01"
