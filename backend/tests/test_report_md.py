from app.db import insert
from builders import add_user_message, make_session, report_json


def finished(app_client, deps, providers):
    sid = make_session(deps)
    insert(deps.conn, "messages", session_id=sid, role="assistant", text="Where were you yesterday?",
           created_at="2026-11-03T15:00:00+00:00")
    add_user_message(deps, sid, "I goed to the beach.")
    providers.report.responses.append(report_json(70, [
        {"said": "I goed", "corrected": "I went", "explanation": "Passado irregular.", "module_id": None}]))
    app_client.post(f"/sessions/{sid}/finish")
    return sid


def test_report_markdown_has_transcript_and_mistakes(app_client, deps, providers):
    sid = finished(app_client, deps, providers)
    r = app_client.get(f"/sessions/{sid}/report.md")
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/markdown")
    text = r.text
    assert text.startswith("# ")
    assert "Past simple x past continuous" in text and "2026-11-03" in text and "70" in text
    assert "**IA:** Where were you yesterday?" in text and "**Você:** I goed to the beach." in text
    assert "I goed → I went — Passado irregular." in text
    assert "How was your weekend?" in text and "Good vocabulary" in text


def test_unfinished_session_has_no_report(app_client, deps):
    sid = make_session(deps)
    add_user_message(deps, sid)
    r = app_client.get(f"/sessions/{sid}/report.md")
    assert r.status_code == 409 and r.json()["error"] == "not_finished"
