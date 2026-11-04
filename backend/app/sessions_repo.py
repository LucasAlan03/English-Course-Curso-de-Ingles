import sqlite3

from app.errors import AppError


def get_session(conn: sqlite3.Connection, session_id: int) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    if row is None:
        raise AppError("session_not_found", 404, "Sessão não encontrada.")
    return row
