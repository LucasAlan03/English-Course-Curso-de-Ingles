from datetime import date, datetime, timedelta, timezone

from app.clock import FixedClock
from app.db import insert
from app.goals import pillars_for_day, streak

D = date(2026, 11, 3)


def add_session(conn, kind, day, user_msgs=1, finished=True):
    sid = insert(conn, "sessions", kind=kind, module_id="m1", started_at=f"{day}T10:00:00+00:00",
                 finished_at=f"{day}T10:30:00+00:00", day=day.isoformat(), is_finished=int(finished))
    for _ in range(user_msgs):
        insert(conn, "messages", session_id=sid, role="user", text="hi", created_at="x")
    return sid


def add_media(conn, type_, day):
    insert(conn, "media_logs", date=day.isoformat(), type=type_,
           category="series" if type_ == "watch" else "hq", title="t", minutes=10, created_at="x")


def complete_day(conn, day):
    add_session(conn, "lesson", day)
    add_session(conn, "writing", day, user_msgs=0)
    add_media(conn, "read", day)
    add_media(conn, "watch", day)


def test_pillars_auto_from_sessions(conn):
    add_session(conn, "lesson", D)
    add_session(conn, "writing", D, user_msgs=0)
    p = pillars_for_day(conn, D)
    assert p == {"grammar": True, "speak": True, "write": True, "read": False, "watch": False}


def test_unfinished_or_silent_sessions_do_not_count(conn):
    add_session(conn, "lesson", D, finished=False)
    add_session(conn, "free", D, user_msgs=0)
    p = pillars_for_day(conn, D)
    assert p["grammar"] is False and p["speak"] is False


def test_pillars_manual_from_media(conn):
    add_media(conn, "read", D)
    add_media(conn, "watch", D)
    p = pillars_for_day(conn, D)
    assert p["read"] is True and p["watch"] is True


def test_streak_counts_consecutive_complete_days(conn):
    for i in range(3):
        complete_day(conn, D - timedelta(days=i))
    assert streak(conn, D) == 3


def test_streak_keeps_yesterday_when_today_incomplete(conn):
    complete_day(conn, D - timedelta(days=1))
    complete_day(conn, D - timedelta(days=2))
    add_session(conn, "lesson", D)  # today only partly done
    assert streak(conn, D) == 2


def test_streak_breaks_on_gap(conn):
    complete_day(conn, D)
    complete_day(conn, D - timedelta(days=2))
    assert streak(conn, D) == 1


def test_session_finished_2330_local_counts_for_local_day(conn):
    clock = FixedClock(datetime(2026, 11, 4, 2, 30, tzinfo=timezone.utc), "America/Sao_Paulo")
    local_day = clock.today()
    sid = insert(conn, "sessions", kind="lesson", module_id="m1", started_at="x",
                 finished_at=clock.now().isoformat(), day=local_day.isoformat(), is_finished=1)
    insert(conn, "messages", session_id=sid, role="user", text="hi", created_at="x")
    assert pillars_for_day(conn, date(2026, 11, 3))["grammar"] is True
    assert pillars_for_day(conn, date(2026, 11, 4))["grammar"] is False
