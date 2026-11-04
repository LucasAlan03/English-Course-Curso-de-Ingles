from app.db import connect, init_schema, insert

EXPECTED = {
    "sessions", "messages", "mistakes", "reviews",
    "listening_items", "media_logs", "api_usage",
}


def tables(conn):
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    return {r["name"] for r in rows}


def test_init_schema_creates_all_tables(tmp_path):
    conn = connect(str(tmp_path / "x" / "app.db"))
    init_schema(conn)
    assert EXPECTED <= tables(conn)


def test_init_schema_idempotent(tmp_path):
    conn = connect(str(tmp_path / "app.db"))
    init_schema(conn)
    init_schema(conn)
    assert EXPECTED <= tables(conn)


def test_insert_returns_id(conn):
    first = insert(conn, "media_logs", date="2026-11-03", type="watch", category="series",
                   title="Friends", minutes=22, created_at="2026-11-03T10:00:00Z")
    second = insert(conn, "media_logs", date="2026-11-03", type="read", category="hq",
                    title="Maus", minutes=15, created_at="2026-11-03T11:00:00Z")
    assert (first, second) == (1, 2)


def test_foreign_keys_enforced(conn):
    import sqlite3
    import pytest
    with pytest.raises(sqlite3.IntegrityError):
        insert(conn, "messages", session_id=999, role="user", text="hi", created_at="x")
