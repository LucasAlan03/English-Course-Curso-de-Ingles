from builders import add_user_message, correct_answers, make_session, report_json

MODULE = "b1_past_simple_continuous"
CORRECT = correct_answers()


def url(exercise_id, module=MODULE):
    return f"/exercises/{module}/{exercise_id}/answer"


def answer_all(client, module=MODULE, wrong=()):
    last = None
    for ex_id, answer in CORRECT.items():
        last = client.post(url(ex_id, module), json={"answer": "nope" if ex_id in wrong else answer, "seconds": 10})
    return last.json()


def test_listing_hides_answers_until_answered(app_client):
    items = app_client.get(f"/modules/{MODULE}/exercises").json()
    assert len(items) == 27
    assert all("answers" not in i and "audio_text" not in i for i in items)
    first = items[0]
    assert first["prompt_pt"] and first["glossary"] == {"park": "parque"}
    assert first["answered"] is False and first["result"] is None


def test_listen_items_have_audio_url_and_others_do_not(app_client):
    items = {i["id"]: i for i in app_client.get(f"/modules/{MODULE}/exercises").json()}
    assert items["e06"]["type"] == "listen" and items["e06"]["audio_url"] == f"/audio/ex_{MODULE}_e06.wav"
    assert items["e01"]["audio_url"] is None


def test_order_words_are_shuffled_deterministically(app_client):
    first = app_client.get(f"/modules/{MODULE}/exercises").json()
    second = app_client.get(f"/modules/{MODULE}/exercises").json()
    order = next(i for i in first if i["type"] == "order")
    assert sorted(order["words"]) == ["cooking", "she", "was"]
    assert [i["words"] for i in first] == [i["words"] for i in second]


def test_answer_is_graded_without_ai(app_client, providers):
    r = app_client.post(url("e01"), json={"answer": CORRECT["e01"], "seconds": 12}).json()
    assert r["correct"] is True and r["correct_answer"] == "went" and r["explanation"]
    assert r["module_completed"] is False and r["score"] is None
    assert providers.report.calls == [] and providers.chat.calls == []


def test_double_submit_keeps_first_answer(app_client, deps):
    app_client.post(url("e01"), json={"answer": "wrong", "seconds": 5})
    again = app_client.post(url("e01"), json={"answer": CORRECT["e01"], "seconds": 5}).json()
    assert again["correct"] is False
    assert deps.conn.execute("SELECT COUNT(*) FROM exercise_attempts").fetchone()[0] == 1


def test_seconds_are_capped_at_180(app_client, deps):
    app_client.post(url("e01"), json={"answer": "went", "seconds": 999})
    assert deps.conn.execute("SELECT seconds, day FROM exercise_attempts").fetchone()[:] == (180, "2026-11-03")


def test_last_answer_completes_module_and_schedules_review(app_client, deps):
    answer_all(app_client, wrong={"e01", "e02", "e03"})
    row = deps.conn.execute("SELECT next_due FROM reviews WHERE module_id = ?", (MODULE,)).fetchone()
    assert row["next_due"] == "2026-11-04"  # first schedule = tomorrow
    assert app_client.get("/modules").json()["levels"][0]["modules"][0]["completed"] is True


def test_completion_response_has_score(app_client):
    last = answer_all(app_client, wrong={"e01", "e02", "e03"})
    assert last["module_completed"] is True and last["score"] == 89 and last["next_due"] == "2026-11-04"


def test_resume_shows_answered_items(app_client):
    app_client.post(url("e01"), json={"answer": "go", "seconds": 3})
    items = app_client.get(f"/modules/{MODULE}/exercises").json()
    assert items[0]["answered"] is True
    assert items[0]["result"] == {"correct": False, "user_answer": "go", "correct_answer": "went",
                                  "explanation": "Past simple para ação terminada."}
    assert items[1]["answered"] is False


def test_unknown_module_or_exercise_404(app_client):
    assert app_client.get("/modules/nope/exercises").status_code == 404
    assert app_client.post(url("e99"), json={"answer": "x", "seconds": 1}).status_code == 404
    assert app_client.post(url("e01", "nope"), json={"answer": "x", "seconds": 1}).status_code == 404


def test_negative_seconds_rejected(app_client):
    assert app_client.post(url("e01"), json={"answer": "x", "seconds": -1}).status_code == 422


def test_report_exercise(app_client, deps):
    r = app_client.post(f"/exercises/{MODULE}/e01/report", json={"note": "duas respostas certas"})
    assert r.json() == {"ok": True}
    assert deps.conn.execute("SELECT exercise_id, note FROM exercise_reports").fetchone()[:] == ("e01", "duas respostas certas")


def test_finish_session_no_longer_schedules(app_client, deps, providers):
    sid = make_session(deps)
    add_user_message(deps, sid)
    providers.report.responses.append(report_json(90))
    body = app_client.post(f"/sessions/{sid}/finish").json()
    assert body["next_due"] is None and "listening_score" not in body and body["final_score"] == 90
    assert deps.conn.execute("SELECT COUNT(*) FROM reviews").fetchone()[0] == 0


def test_completion_is_claimed_only_by_the_request_that_saved_the_last_answer(app_client, deps, monkeypatch):
    from app.routes import exercises as routes
    answer_all(app_client, wrong=set())  # 27 answered, review scheduled once
    deps.conn.execute("DELETE FROM reviews")
    deps.conn.commit()
    # Two overlapping taps: the second read its "before" count while the first had not inserted yet.
    real, calls = routes.lesson_attempts, []

    def stale_first_read(d, module_id):
        rows = real(d, module_id)
        calls.append(1)
        return {k: v for k, v in rows.items() if k != "e27"} if len(calls) == 1 else rows

    monkeypatch.setattr(routes, "lesson_attempts", stale_first_read)
    again = app_client.post(url("e27"), json={"answer": CORRECT["e27"], "seconds": 1}).json()
    assert again["module_completed"] is False
    assert deps.conn.execute("SELECT COUNT(*) FROM reviews").fetchone()[0] == 0
