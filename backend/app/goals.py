import sqlite3
from datetime import date, timedelta

PILLARS = ("grammar", "speak", "write", "read", "watch")


def _exists(conn: sqlite3.Connection, sql: str, *args) -> bool:
    return conn.execute(f"SELECT EXISTS({sql})", args).fetchone()[0] == 1


def pillars_for_day(conn: sqlite3.Connection, day: date) -> dict[str, bool]:
    d = day.isoformat()
    finished = "FROM sessions s WHERE s.is_finished = 1 AND s.day = ?"
    return {
        "grammar": _exists(conn, f"SELECT 1 {finished} AND s.kind IN ('lesson','review')", d),
        "speak": _exists(
            conn,
            f"SELECT 1 {finished} AND s.kind IN ('lesson','review','free') AND EXISTS("
            "SELECT 1 FROM messages m WHERE m.session_id = s.id AND m.role = 'user')",
            d,
        ),
        "write": _exists(conn, f"SELECT 1 {finished} AND s.kind = 'writing'", d),
        "read": _exists(conn, "SELECT 1 FROM media_logs WHERE date = ? AND type = 'read'", d),
        "watch": _exists(conn, "SELECT 1 FROM media_logs WHERE date = ? AND type = 'watch'", d),
    }


def _complete(conn: sqlite3.Connection, day: date) -> bool:
    return all(pillars_for_day(conn, day).values())


def streak(conn: sqlite3.Connection, today: date) -> int:
    """Consecutive fully completed days ending today, or yesterday if today is not done yet."""
    day = today if _complete(conn, today) else today - timedelta(days=1)
    count = 0
    while _complete(conn, day):
        count += 1
        day -= timedelta(days=1)
    return count
