import sqlite3

from fastapi import APIRouter

router = APIRouter()


def add_word(conn: sqlite3.Connection, word: str, sentence: str, translation: str, note: str, source: str,
             now: str) -> int:
    """Save a word for the Anki list; a repeated (word, sentence) keeps the first row."""
    conn.execute(
        "INSERT OR IGNORE INTO words (word, sentence, translation, note, source, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (word, sentence, translation, note, source, now),
    )
    conn.commit()
    return conn.execute("SELECT id FROM words WHERE word = ? AND sentence = ?", (word, sentence)).fetchone()["id"]
