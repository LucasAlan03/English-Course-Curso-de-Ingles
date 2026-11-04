from datetime import date

from app.db import insert
from app.goals import pillars_for_day
from builders import make_session, writing_json

TEXT = "Last weekend I goed to the beach with my family and we ate a lot."


def count(deps, table, where="1=1"):
    return deps.conn.execute(f"SELECT COUNT(*) FROM {table} WHERE {where}").fetchone()[0]


def new_prompt(app_client, providers, topic="Describe your last weekend."):
    providers.chat.responses.append(topic)
    return app_client.post("/writing/prompt").json()


def test_prompt_creates_writing_session(app_client, deps, providers):
    body = new_prompt(app_client, providers)
    assert body["prompt"] == "Describe your last weekend."
    row = deps.conn.execute("SELECT kind, topic, module_id FROM sessions WHERE id = ?", (body["session_id"],)).fetchone()
    assert (row["kind"], row["topic"], row["module_id"]) == ("writing", "Describe your last weekend.", None)
    assert "B1" in providers.chat.calls[0][0]


def test_new_prompt_avoids_recent_topics(app_client, providers):
    new_prompt(app_client, providers, "Describe your last weekend.")
    new_prompt(app_client, providers, "Give advice to a friend.")
    assert "Describe your last weekend." in providers.chat.calls[1][0]


def test_submit_returns_feedback_and_saves_mistakes(app_client, deps, providers):
    sid = new_prompt(app_client, providers)["session_id"]
    providers.report.responses.append(writing_json())
    r = app_client.post("/writing/submit", json={"session_id": sid, "text": TEXT})
    assert r.status_code == 200
    body = r.json()
    assert body["corrected_text"].startswith("Last weekend") and body["score"] == 75
    saved = deps.conn.execute("SELECT module_id, said FROM mistakes").fetchall()
    assert [(m["module_id"], m["said"]) for m in saved] == [("b1_past_simple_continuous", "I goed to the beach")]
    system = providers.report.calls[0][0]
    assert TEXT in system and "Describe your last weekend." in system


def test_submit_marks_write_pillar(app_client, deps, providers):
    sid = new_prompt(app_client, providers)["session_id"]
    assert pillars_for_day(deps.conn, date(2026, 11, 3))["write"] is False
    providers.report.responses.append(writing_json())
    app_client.post("/writing/submit", json={"session_id": sid, "text": TEXT})
    assert pillars_for_day(deps.conn, date(2026, 11, 3))["write"] is True


def test_submit_empty_or_short_text_422_and_no_ai_call(app_client, deps, providers):
    sid = new_prompt(app_client, providers)["session_id"]
    for text in ["", "   ", "too short"]:
        r = app_client.post("/writing/submit", json={"session_id": sid, "text": text})
        assert r.status_code == 422 and r.json()["error"] == "text_too_short"
    assert providers.report.calls == []
    assert deps.conn.execute("SELECT is_finished FROM sessions WHERE id = ?", (sid,)).fetchone()[0] == 0


def test_submit_twice_is_409(app_client, providers):
    sid = new_prompt(app_client, providers)["session_id"]
    providers.report.responses.append(writing_json())
    assert app_client.post("/writing/submit", json={"session_id": sid, "text": TEXT}).status_code == 200
    assert app_client.post("/writing/submit", json={"session_id": sid, "text": TEXT}).status_code == 409


def test_invalid_ai_output_saves_nothing(app_client, deps, providers):
    sid = new_prompt(app_client, providers)["session_id"]
    providers.report.responses.extend(["nope", "nope again"])
    r = app_client.post("/writing/submit", json={"session_id": sid, "text": TEXT})
    assert r.status_code == 502 and r.json()["error"] == "invalid_ai_output"
    assert count(deps, "mistakes") == 0
    assert deps.conn.execute("SELECT is_finished FROM sessions WHERE id = ?", (sid,)).fetchone()[0] == 0


def test_wrong_session_kind_or_unknown_session(app_client, deps):
    lesson = make_session(deps)
    assert app_client.post("/writing/submit", json={"session_id": lesson, "text": TEXT}).status_code == 400
    assert app_client.post("/writing/submit", json={"session_id": 999, "text": TEXT}).status_code == 404


def test_writing_mistakes_pull_reviews_forward(app_client, deps, providers):
    insert(deps.conn, "reviews", module_id="b1_past_simple_continuous", next_due="2026-12-01",
           interval_days=20, ease=2.5, repetitions=3)
    old = make_session(deps)
    for _ in range(2):
        insert(deps.conn, "mistakes", session_id=old, module_id="b1_past_simple_continuous", said="x",
               corrected="y", explanation="z", created_at=deps.clock.now().isoformat())
    sid = new_prompt(app_client, providers)["session_id"]
    providers.report.responses.append(writing_json())
    app_client.post("/writing/submit", json={"session_id": sid, "text": TEXT})
    due = deps.conn.execute("SELECT next_due FROM reviews").fetchone()[0]
    assert due == "2026-11-04"
