from app.db import insert
from builders import complete_module, make_session

B1_A, B1_B, B2_A = "b1_past_simple_continuous", "b1_futures", "b2_passive_voice"


def complete_lesson(deps, module_id):
    complete_module(deps, module_id)


def add_review(deps, module_id, next_due):
    insert(deps.conn, "reviews", module_id=module_id, next_due=next_due, interval_days=3, ease=2.5, repetitions=1)


def test_modules_lists_all_with_progress(app_client, deps):
    complete_lesson(deps, B1_A)
    body = app_client.get("/modules").json()
    levels = {lv["level"]: lv for lv in body["levels"]}
    assert [lv["level"] for lv in body["levels"]] == ["B1", "B2"]
    assert (levels["B1"]["total"], levels["B1"]["completed"]) == (2, 1)
    assert (levels["B2"]["total"], levels["B2"]["completed"]) == (1, 0)
    assert [m["id"] for m in levels["B1"]["modules"]] == [B1_A, B1_B]
    assert [m["completed"] for m in levels["B1"]["modules"]] == [True, False]


def test_unfinished_lessons_do_not_count_as_completed(app_client, deps):
    make_session(deps, kind="lesson", module_id=B1_A, is_finished=0)
    make_session(deps, kind="review", module_id=B1_B, is_finished=1)
    levels = app_client.get("/modules").json()["levels"]
    assert levels[0]["completed"] == 0


def test_module_detail_and_unknown_module_404(app_client, deps):
    complete_lesson(deps, B1_A)
    ok = app_client.get(f"/modules/{B1_A}").json()
    assert ok["id"] == B1_A and ok["theory_md"] and ok["scenario"]["goal"] == "Order a coffee"
    assert ok["completed"] is True
    missing = app_client.get("/modules/nope")
    assert missing.status_code == 404 and missing.json()["error"] == "module_not_found"


def test_home_reviews_due_sorted_overdue_first(app_client, deps):
    add_review(deps, B1_B, "2026-11-03")
    add_review(deps, B1_A, "2026-11-01")
    add_review(deps, B2_A, "2026-11-05")  # not due yet
    add_review(deps, "ghost_module", "2026-10-01")  # no longer in the curriculum
    due = app_client.get("/home").json()["reviews_due"]
    assert [(r["module_id"], r["overdue_days"]) for r in due] == [(B1_A, 2), (B1_B, 0)]
    assert due[0]["title"] == "Past simple x past continuous" and due[0]["next_due"] == "2026-11-01"


def test_home_next_module_skips_completed(app_client, deps):
    assert app_client.get("/home").json()["next_module"]["id"] == B1_A
    complete_lesson(deps, B1_A)
    assert app_client.get("/home").json()["next_module"]["id"] == B1_B
    complete_lesson(deps, B1_B)
    assert app_client.get("/home").json()["next_module"] is None  # B2 waits for the B1 exam
    insert(deps.conn, "exam_runs", level="B1", question_ids="[]", started_at="x", finished_at="y", score=80, passed=1)
    nxt = app_client.get("/home").json()["next_module"]
    assert (nxt["id"], nxt["level"]) == (B2_A, "B2")
    complete_lesson(deps, B2_A)
    assert app_client.get("/home").json()["next_module"] is None


def test_home_includes_day_plan_streak_usage(app_client, deps):
    insert(deps.conn, "media_logs", date="2026-11-03", type="read", category="hq", title="Maus",
           minutes=10, created_at="x")
    body = app_client.get("/home").json()
    read = next(b for b in body["today"]["blocks"] if b["key"] == "read")
    assert (read["minutes"], read["status"]) == (10, "pending")
    assert body["streak"] == 0
    assert body["usage"]["level"] == "ok"
