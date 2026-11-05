from builders import add_user_message, make_session, report_json

MODULE = "b1_past_simple_continuous"


def test_teach_session_needs_a_module(app_client):
    assert app_client.post("/sessions", json={"kind": "teach"}).status_code == 422
    assert app_client.post("/sessions", json={"kind": "teach", "module_id": "nope"}).status_code == 404


def test_teach_session_uses_the_confused_student_persona(app_client, providers):
    sid = app_client.post("/sessions", json={"kind": "teach", "module_id": MODULE}).json()["id"]
    providers.chat.responses.append("Hi! I never understand when to use 'was going'. Can you help me?")
    r = app_client.post(f"/sessions/{sid}/turn", data={"text": "Let me explain the past continuous."})
    assert r.status_code == 200
    system = providers.chat.calls[0][0]
    assert "Past simple x past continuous" in system and "confused" in system


def test_teach_finish_reports_without_scheduling(app_client, deps, providers):
    sid = make_session(deps, kind="teach")
    add_user_message(deps, sid, "We use was plus ing for an action in progress.")
    providers.report.responses.append(report_json(85))
    body = app_client.post(f"/sessions/{sid}/finish").json()
    assert body["conversation_score"] == 85 and body["next_due"] is None
    assert deps.conn.execute("SELECT COUNT(*) FROM reviews").fetchone()[0] == 0
    assert "explains" in providers.report.calls[0][0]
