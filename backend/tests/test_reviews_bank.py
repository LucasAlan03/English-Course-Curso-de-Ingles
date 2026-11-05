from app.content import Exercise
from app.db import insert
from app.exercises import pick_review
from builders import correct_answers, valid_exercises

MODULE = "b1_past_simple_continuous"
CORRECT = correct_answers()
EXERCISES = [Exercise(**e) for e in valid_exercises()]


def attempt(conn, exercise_id, correct, created_at, kind="lesson", run_id=None):
    insert(conn, "exercise_attempts", module_id=MODULE, exercise_id=exercise_id, kind=kind, run_id=run_id,
           answer="x", correct=correct, seconds=5, day=created_at[:10], created_at=created_at)


def test_missed_exercises_come_first_newest_mistake_first(conn):
    for i in range(1, 28):
        attempt(conn, f"e{i:02d}", 1, f"2026-11-01T10:{i:02d}:00+00:00")
    conn.execute("UPDATE exercise_attempts SET correct = 0 WHERE exercise_id IN ('e05', 'e20')")
    conn.execute("UPDATE exercise_attempts SET created_at = '2026-11-02T09:00:00+00:00' WHERE exercise_id = 'e05'")
    picked = [e.id for e in pick_review(conn, MODULE, EXERCISES)]
    assert picked[:2] == ["e05", "e20"]
    assert picked[2:] == ["e01", "e02", "e03", "e04", "e06", "e07", "e08"]  # then oldest attempts


def test_latest_attempt_decides_whether_it_was_missed(conn):
    attempt(conn, "e01", 0, "2026-11-01T10:00:00+00:00")
    attempt(conn, "e01", 1, "2026-11-02T10:00:00+00:00", kind="review", run_id=1)
    picked = [e.id for e in pick_review(conn, MODULE, EXERCISES)]
    assert picked[0] != "e01"


def test_never_attempted_counts_as_oldest(conn):
    attempt(conn, "e01", 1, "2026-11-01T10:00:00+00:00")
    picked = [e.id for e in pick_review(conn, MODULE, EXERCISES)]
    assert "e01" not in picked and picked[0] == "e02" and len(picked) == 9


def start(app_client):
    return app_client.post(f"/reviews/{MODULE}/start").json()


def test_start_returns_nine_unanswered_items_without_answers(app_client):
    body = start(app_client)
    assert isinstance(body["run_id"], int) and len(body["exercises"]) == 9
    assert all(not i["answered"] and "answers" not in i for i in body["exercises"])


def answer_run(app_client, body, wrong=()):
    last = None
    for item in body["exercises"]:
        answer = "nope" if item["id"] in wrong else CORRECT[item["id"]]
        last = app_client.post(f"/exercises/{MODULE}/{item['id']}/answer",
                               json={"answer": answer, "seconds": 8, "run_id": body["run_id"]}).json()
    return last


def test_full_review_moves_next_due_forward(app_client, deps, providers):
    insert(deps.conn, "reviews", module_id=MODULE, next_due="2026-11-03", interval_days=1, ease=2.5, repetitions=0)
    last = answer_run(app_client, start(app_client))
    assert last["module_completed"] is True and last["score"] == 100 and last["next_due"] == "2026-11-06"
    assert providers.report.calls == [] and providers.chat.calls == []
    row = deps.conn.execute("SELECT score, finished_at FROM review_runs").fetchone()
    assert row["score"] == 100 and row["finished_at"]


def test_review_answers_do_not_touch_the_lesson(app_client, deps):
    body = start(app_client)
    answer_run(app_client, body)
    items = app_client.get(f"/modules/{MODULE}/exercises").json()
    assert not any(i["answered"] for i in items)


def test_review_double_submit_keeps_first(app_client, deps):
    body = start(app_client)
    item = body["exercises"][0]
    url = f"/exercises/{MODULE}/{item['id']}/answer"
    app_client.post(url, json={"answer": "nope", "seconds": 1, "run_id": body["run_id"]})
    again = app_client.post(url, json={"answer": CORRECT[item["id"]], "seconds": 1, "run_id": body["run_id"]}).json()
    assert again["correct"] is False


def test_unknown_run_is_404(app_client):
    r = app_client.post(f"/exercises/{MODULE}/e01/answer", json={"answer": "went", "seconds": 1, "run_id": 999})
    assert r.status_code == 404


def test_exercise_outside_the_run_is_404(app_client):
    body = start(app_client)
    outside = next(i for i in CORRECT if i not in {e["id"] for e in body["exercises"]})
    r = app_client.post(f"/exercises/{MODULE}/{outside}/answer",
                        json={"answer": "x", "seconds": 1, "run_id": body["run_id"]})
    assert r.status_code == 404


def test_review_of_module_without_exercises_is_404(app_client):
    assert app_client.post("/reviews/b1_futures/start").status_code == 404
