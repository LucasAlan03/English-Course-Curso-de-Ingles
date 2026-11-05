from datetime import date, datetime, timezone

from app.clock import FixedClock
from app.daily_plan import BLOCKS, day_plan, streak
from app.db import insert
from builders import complete_module, correct_answers

DAY = date(2026, 11, 3)


def blocks(plan):
    return {b["key"]: b for b in plan["blocks"]}


def grammar_seconds(deps, seconds, day="2026-11-03", exercise="e01", module="b1_futures"):
    insert(deps.conn, "exercise_attempts", module_id=module, exercise_id=exercise, kind="lesson", answer="x",
           correct=1, seconds=seconds, day=day, created_at=f"{day}T12:00:00+00:00")


def media(deps, kind, minutes, day="2026-11-03"):
    category = "video" if kind == "watch" else "book"
    insert(deps.conn, "media_logs", date=day, type=kind, category=category, title="t", minutes=minutes,
           created_at="x")


def external_call(deps, minutes, day="2026-11-03"):
    insert(deps.conn, "call_logs", date=day, source="Be Confident", minutes=minutes, created_at="x")


def song_chunk_done(deps, day="2026-11-03"):
    song = insert(deps.conn, "songs", title="s", artist="a", lyrics="la la", is_current=1, created_at="x")
    chunk = insert(deps.conn, "song_chunks", song_id=song, idx=0, text="la la")
    for kind in ("dictation", "shadow"):
        insert(deps.conn, "song_practice", song_id=song, chunk_id=chunk, kind=kind, text="la", score=100, day=day,
               created_at="x")


def test_empty_day_starts_with_grammar(deps):
    plan = day_plan(deps, DAY)
    assert [b["key"] for b in plan["blocks"]] == list(BLOCKS)
    assert plan["current"] == "grammar" and plan["complete"] is False
    assert blocks(plan)["grammar"] == {"key": "grammar", "title": "Gramática", "status": "current",
                                       "minutes": 0, "target": 20}
    assert blocks(plan)["music"]["status"] == "pending" and blocks(plan)["music"]["target"] is None


def test_twenty_minutes_of_answers_finish_grammar(deps):
    for i in range(1, 8):
        grammar_seconds(deps, 180, exercise=f"e{i:02d}")  # 7 x 3 min = 21 min
    plan = day_plan(deps, DAY)
    assert blocks(plan)["grammar"]["status"] == "done" and blocks(plan)["grammar"]["minutes"] == 21
    assert plan["current"] == "music"


def test_finishing_a_module_today_finishes_grammar(deps):
    complete_module(deps, "b1_futures")  # 27 x 10 s = 4 min
    assert blocks(day_plan(deps, DAY))["grammar"]["status"] == "done"


def test_finishing_an_exam_today_finishes_grammar(deps):
    insert(deps.conn, "exam_runs", level="B1", question_ids="[]", started_at="x",
           finished_at="2026-11-03T20:00:00+00:00", score=50, passed=0)
    assert blocks(day_plan(deps, DAY))["grammar"]["status"] == "done"


def test_exam_seconds_count_as_grammar_time(deps):
    run = insert(deps.conn, "exam_runs", level="B1", question_ids="[]", started_at="x")
    for i in range(7):
        insert(deps.conn, "exam_attempts", run_id=run, question_id=f"q{i:02d}", answer="x", correct=1, seconds=180,
               day="2026-11-03", created_at="x")
    assert blocks(day_plan(deps, DAY))["grammar"]["status"] == "done"


def test_skip_and_unskip_music(app_client, deps):
    complete_module(deps, "b1_futures")
    assert app_client.post("/today/music/skip").status_code == 200
    plan = app_client.get("/today").json()
    assert blocks(plan)["music"]["status"] == "skipped" and plan["current"] == "call1"
    app_client.post("/today/music/unskip")
    assert app_client.get("/today").json()["current"] == "music"


def test_unknown_block_is_400(app_client):
    assert app_client.post("/today/nap/skip").status_code == 400


def test_reading_logged_early_is_done_but_current_stays(deps):
    complete_module(deps, "b1_futures")
    media(deps, "read", 40)
    plan = day_plan(deps, DAY)
    assert blocks(plan)["read"]["status"] == "done" and plan["current"] == "music"


def test_music_done_with_dictation_and_shadow(deps):
    song_chunk_done(deps)
    assert blocks(day_plan(deps, DAY))["music"]["status"] == "done"


def test_twenty_five_external_minutes_fill_both_calls(deps):
    external_call(deps, 25)
    b = blocks(day_plan(deps, DAY))
    assert (b["call1"]["status"], b["call1"]["minutes"]) == ("done", 10)
    assert (b["call2"]["status"], b["call2"]["minutes"]) == ("done", 10)


def test_fifteen_minutes_fill_call1_and_half_of_call2(deps):
    external_call(deps, 15)
    b = blocks(day_plan(deps, DAY))
    assert b["call1"]["status"] == "done" and (b["call2"]["status"], b["call2"]["minutes"]) == ("pending", 5)


def test_answer_late_at_night_counts_for_the_local_day(app_client, deps):
    deps.clock = FixedClock(datetime(2026, 11, 4, 2, 30, tzinfo=timezone.utc), "America/Sao_Paulo")
    answer = correct_answers()["e01"]
    app_client.post("/exercises/b1_past_simple_continuous/e01/answer", json={"answer": answer, "seconds": 120})
    assert blocks(day_plan(deps, DAY))["grammar"]["minutes"] == 2
    assert blocks(day_plan(deps, date(2026, 11, 4)))["grammar"]["minutes"] == 0


def full_day(deps, day="2026-11-03"):
    complete_module(deps, f"m_{day}", day=day)
    song_chunk_done(deps, day)
    external_call(deps, 20, day)
    media(deps, "watch", 45, day)
    media(deps, "read", 40, day)
    insert(deps.conn, "day_state", date=day, block="anki", skipped=0, checked=1)


def test_all_blocks_done_complete_the_day_and_streak(app_client, deps):
    full_day(deps)
    body = app_client.get("/today").json()
    assert body["complete"] is True and body["current"] is None and body["streak"] == 1


def test_streak_counts_back_and_tolerates_unfinished_today(deps):
    full_day(deps, "2026-11-01")
    full_day(deps, "2026-11-02")
    assert streak(deps, DAY) == 2  # today not done yet: count from yesterday
    full_day(deps, "2026-11-03")
    assert streak(deps, DAY) == 3


def test_a_skipped_block_keeps_the_day_incomplete(app_client, deps):
    full_day(deps)
    deps.conn.execute("DELETE FROM day_state WHERE block = 'anki'")
    deps.conn.commit()
    app_client.post("/today/anki/skip")
    assert app_client.get("/today").json()["complete"] is False


def test_anki_check_endpoint(app_client):
    app_client.post("/today/anki", json={"checked": True})
    assert blocks(app_client.get("/today").json())["anki"]["status"] == "done"
    app_client.post("/today/anki", json={"checked": False})
    assert blocks(app_client.get("/today").json())["anki"]["status"] != "done"


def test_home_has_the_plan_instead_of_pillars(app_client):
    body = app_client.get("/home").json()
    assert "pillars" not in body and body["today"]["current"] == "grammar" and body["streak"] == 0
