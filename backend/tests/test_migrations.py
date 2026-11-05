from app.db import insert
from app.migrations import MODULE_MIGRATION, ensure_columns, migrate_module_ids


def add_review(conn, module_id, due):
    insert(conn, "reviews", module_id=module_id, next_due=due, interval_days=3, ease=2.5, repetitions=1)


def test_migration_moves_reviews_sessions_and_mistakes(conn):
    add_review(conn, "b1_futures", "2026-11-10")
    sid = insert(conn, "sessions", kind="lesson", module_id="b1_futures", started_at="x")
    insert(conn, "mistakes", session_id=sid, module_id="b1_futures", said="a", corrected="b", explanation="c",
           created_at="x")
    migrate_module_ids(conn)
    migrate_module_ids(conn)
    assert conn.execute("SELECT module_id FROM reviews").fetchone()[0] == "b1_future_will"
    assert conn.execute("SELECT module_id FROM sessions WHERE id=?", (sid,)).fetchone()[0] == "b1_future_will"
    assert conn.execute("SELECT module_id FROM mistakes").fetchone()[0] == "b1_future_will"


def test_migration_keeps_earliest_due_when_both_ids_exist(conn):
    add_review(conn, "b1_futures", "2026-11-08")
    add_review(conn, "b1_future_will", "2026-11-12")
    migrate_module_ids(conn)
    rows = conn.execute("SELECT module_id, next_due FROM reviews").fetchall()
    assert [tuple(r) for r in rows] == [("b1_future_will", "2026-11-08")]


def test_migration_keeps_new_row_when_it_is_earlier(conn):
    add_review(conn, "b1_futures", "2026-11-12")
    add_review(conn, "b1_future_will", "2026-11-08")
    migrate_module_ids(conn)
    rows = conn.execute("SELECT module_id, next_due FROM reviews").fetchall()
    assert [tuple(r) for r in rows] == [("b1_future_will", "2026-11-08")]


def test_map_covers_the_18_combined_modules():
    assert len(MODULE_MIGRATION) == 18
    assert MODULE_MIGRATION["b1_past_simple_continuous"] == "b1_past_simple"


def test_ensure_columns_adds_only_missing(conn):
    ensure_columns(conn, "media_logs", {"count": "INTEGER", "url": "TEXT"})
    ensure_columns(conn, "media_logs", {"count": "INTEGER", "url": "TEXT"})
    cols = {r[1] for r in conn.execute("PRAGMA table_info(media_logs)")}
    assert {"count", "url"} <= cols
