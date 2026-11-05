from app.content import ExamQuestion, validate_exam
from builders import complete_module, exam_answers, valid_exam

B1 = ["b1_past_simple_continuous", "b1_futures"]
ANSWERS = exam_answers(B1)


def models(data):
    return [ExamQuestion(**q) for q in data]


def test_valid_exam_passes():
    assert validate_exam("B1", models(valid_exam(B1)), B1) == []


def test_exam_needs_exactly_40():
    assert any("40" in p for p in validate_exam("B1", models(valid_exam(B1, size=41)), B1))


def test_exam_must_cover_every_module():
    data = valid_exam(B1)
    for q in data:
        q["module_id"] = B1[0]
    assert any(B1[1] in p for p in validate_exam("B1", models(data), B1))


def test_exam_question_module_must_belong_to_level():
    data = valid_exam(B1)
    data[0]["module_id"] = "b2_passive_voice"
    assert any("q01" in p for p in validate_exam("B1", models(data), B1))


def test_exam_item_rules_apply():
    data = valid_exam(B1)
    data[0]["glossary"] = {"went": "foi"}
    assert any("q01" in p for p in validate_exam("B1", models(data), B1))


def test_too_many_choice_questions_reported():
    data = valid_exam(B1)
    for q in data[:21]:
        q.update(valid_exam(B1)[0] | {"id": q["id"], "module_id": q["module_id"],
                                      "prompt": f"Yesterday I ___ to the park ({q['id']})."})
    assert any("choice" in p for p in validate_exam("B1", models(data), B1))


def test_b2_module_is_locked_until_b1_exam_passed(app_client):
    r = app_client.get("/modules/b2_passive_voice/exercises")
    assert r.status_code == 403 and r.json()["error"] == "level_locked"
    r = app_client.post("/exercises/b2_passive_voice/e01/answer", json={"answer": "x", "seconds": 1})
    assert r.status_code == 403


def test_modules_list_shows_locks_and_exam_status(app_client, deps):
    complete_module(deps, B1[0])
    levels = {lv["level"]: lv for lv in app_client.get("/modules").json()["levels"]}
    assert levels["B1"]["unlocked"] is True and levels["B2"]["unlocked"] is False
    assert levels["B1"]["exam"] == {"available": False, "missing_modules": 1, "passed": False,
                                    "best_score": None, "open_run_id": None}


def test_exam_start_is_locked_while_a_module_is_incomplete(app_client, deps):
    complete_module(deps, B1[0])
    r = app_client.post("/exams/B1/start")
    assert r.status_code == 409 and r.json()["error"] == "exam_locked"


def start(app_client, deps):
    for m in B1:
        complete_module(deps, m)
    return app_client.post("/exams/B1/start").json()


def test_exam_start_returns_30_questions_without_answers(app_client, deps):
    body = start(app_client, deps)
    assert len(body["questions"]) == 30 and len({q["id"] for q in body["questions"]}) == 30
    assert all("answers" not in q and "module_id" not in q and not q["answered"] for q in body["questions"])


def test_starting_twice_returns_the_open_run(app_client, deps):
    first = start(app_client, deps)
    again = app_client.post("/exams/B1/start").json()
    assert again["run_id"] == first["run_id"]
    assert [q["id"] for q in again["questions"]] == [q["id"] for q in first["questions"]]


def answer(app_client, run_id, qid, text, seconds=20):
    return app_client.post(f"/exams/runs/{run_id}/{qid}/answer", json={"answer": text, "seconds": seconds})


def take(app_client, body, wrong_count):
    last = None
    for i, q in enumerate(body["questions"]):
        last = answer(app_client, body["run_id"], q["id"], "nope" if i < wrong_count else ANSWERS[q["id"]])
    return last.json()


def test_answers_give_no_feedback_while_running(app_client, deps):
    body = start(app_client, deps)
    r = answer(app_client, body["run_id"], body["questions"][0]["id"], "nope", 5).json()
    assert r == {"saved": True, "finished": False, "score": None, "passed": None}


def test_23_of_30_passes_and_unlocks_b2(app_client, deps, providers):
    last = take(app_client, start(app_client, deps), wrong_count=7)
    assert last == {"saved": True, "finished": True, "score": 77, "passed": True}
    levels = {lv["level"]: lv for lv in app_client.get("/modules").json()["levels"]}
    assert levels["B2"]["unlocked"] is True and levels["B1"]["exam"]["passed"] is True
    assert levels["B1"]["exam"]["best_score"] == 77
    assert app_client.get("/modules/b2_passive_voice/exercises").status_code == 200
    assert providers.report.calls == [] and providers.chat.calls == []


def test_22_of_30_fails_and_lists_the_wrong_ones(app_client, deps):
    body = start(app_client, deps)
    last = take(app_client, body, wrong_count=8)
    assert last["finished"] is True and last["passed"] is False and last["score"] == 73
    run = app_client.get(f"/exams/runs/{body['run_id']}").json()
    wrong = [r for r in run["results"] if not r["correct"]]
    assert len(wrong) == 8 and wrong[0]["module_title"] in {"Past simple x past continuous", "Futures"}
    assert wrong[0]["correct_answer"] and wrong[0]["explanation"] and wrong[0]["user_answer"] == "nope"
    levels = {lv["level"]: lv for lv in app_client.get("/modules").json()["levels"]}
    assert levels["B2"]["unlocked"] is False


def test_a_failed_exam_can_be_retaken_with_a_new_run(app_client, deps):
    body = start(app_client, deps)
    take(app_client, body, wrong_count=10)
    again = app_client.post("/exams/B1/start").json()
    assert again["run_id"] != body["run_id"] and len(again["questions"]) == 30


def test_running_exam_hides_results(app_client, deps):
    body = start(app_client, deps)
    run = app_client.get(f"/exams/runs/{body['run_id']}").json()
    assert run["finished"] is False and run["results"] is None


def test_exam_double_submit_keeps_first_and_seconds_capped(app_client, deps):
    body = start(app_client, deps)
    qid = body["questions"][0]["id"]
    answer(app_client, body["run_id"], qid, "nope", 999)
    answer(app_client, body["run_id"], qid, ANSWERS[qid], 1)
    rows = deps.conn.execute("SELECT correct, seconds, day FROM exam_attempts").fetchall()
    assert [tuple(r) for r in rows] == [(0, 180, "2026-11-03")]


def test_question_outside_the_run_is_404(app_client, deps):
    body = start(app_client, deps)
    inside = {q["id"] for q in body["questions"]}
    outside = next(q for q in ANSWERS if q not in inside)
    assert answer(app_client, body["run_id"], outside, "x").status_code == 404
    assert answer(app_client, 999, "q01", "x").status_code == 404


def test_unknown_level_is_404(app_client):
    assert app_client.post("/exams/A2/start").status_code == 404


def test_exam_of_locked_level_is_locked(app_client):
    assert app_client.post("/exams/B2/start").status_code == 409
