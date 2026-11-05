import csv
import io
import sqlite3

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from pydantic import BaseModel, Field, field_validator

from app.ai.translate import translate
from app.deps import AppDeps, get_deps
from app.errors import AppError

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


class TranslateIn(BaseModel):
    word: str = Field(max_length=60)
    sentence: str = Field(default="", max_length=500)

    @field_validator("word")
    @classmethod
    def word_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("word is required")
        return value


class WordIn(BaseModel):
    word: str = Field(min_length=1, max_length=60)
    sentence: str = Field(default="", max_length=500)
    translation: str = ""
    note: str = ""
    source: str = "tap"


def _row(r) -> dict:
    return {k: r[k] for k in ("id", "word", "sentence", "translation", "note", "source", "created_at")}


@router.post("/translate")
def translate_word(body: TranslateIn, deps: AppDeps = Depends(get_deps)):
    return translate(deps, body.word, body.sentence)


@router.get("/words")
def list_words(deps: AppDeps = Depends(get_deps)):
    return [_row(r) for r in deps.conn.execute("SELECT * FROM words ORDER BY id DESC")]


@router.post("/words")
def save_word(body: WordIn, deps: AppDeps = Depends(get_deps)):
    word_id = add_word(deps.conn, body.word.strip(), body.sentence.strip(), body.translation, body.note,
                       body.source, deps.clock.now().isoformat())
    return _row(deps.conn.execute("SELECT * FROM words WHERE id = ?", (word_id,)).fetchone())


@router.delete("/words/{word_id}")
def delete_word(word_id: int, deps: AppDeps = Depends(get_deps)):
    if not deps.conn.execute("DELETE FROM words WHERE id = ?", (word_id,)).rowcount:
        raise AppError("word_not_found", 404, "Palavra não encontrada.")
    deps.conn.commit()
    return {"deleted": word_id}


@router.get("/words/export.csv")
def export_words(deps: AppDeps = Depends(get_deps)):
    out = io.StringIO()
    writer = csv.writer(out, delimiter=";", lineterminator="\n")
    for r in deps.conn.execute("SELECT * FROM words ORDER BY id"):
        front = r["word"] + (f" — {r['sentence']}" if r["sentence"] else "")
        back = r["translation"] + (f" ({r['note']})" if r["note"] else "")
        writer.writerow([front, back])
    return Response(out.getvalue(), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": 'attachment; filename="palavras.csv"'})
