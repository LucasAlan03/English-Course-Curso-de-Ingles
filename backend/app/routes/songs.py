import json
from datetime import timezone

from fastapi import APIRouter, Depends, File, UploadFile
from pydantic import BaseModel, Field

from app.ai.song_grammar import tag_song
from app.db import insert
from app.deps import AppDeps, get_deps
from app.errors import AppError, EmptyTranscript
from app.songs import lyrics_text, split_chunks, word_diff
from app.speech import heard_words

router = APIRouter()


class SongIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    artist: str = Field(min_length=1, max_length=200)
    link: str | None = None
    lyrics: str = Field(max_length=20000)


class DictationIn(BaseModel):
    text: str


def _song(deps: AppDeps, song_id: int):
    row = deps.conn.execute("SELECT * FROM songs WHERE id = ?", (song_id,)).fetchone()
    if row is None:
        raise AppError("song_not_found", 404, "Música não encontrada.")
    return row


def _chunk(deps: AppDeps, chunk_id: int):
    row = deps.conn.execute("SELECT * FROM song_chunks WHERE id = ?", (chunk_id,)).fetchone()
    if row is None:
        raise AppError("chunk_not_found", 404, "Trecho não encontrado.")
    return row


def _practice(deps: AppDeps, song_id: int) -> dict[int, dict[str, str]]:
    """chunk_id -> {kind: latest day}."""
    out: dict[int, dict[str, str]] = {}
    for r in deps.conn.execute("SELECT chunk_id, kind, MAX(day) AS day FROM song_practice WHERE song_id = ? "
                               "AND chunk_id IS NOT NULL GROUP BY chunk_id, kind", (song_id,)):
        out.setdefault(r["chunk_id"], {})[r["kind"]] = r["day"]
    return out


def _is_done(kinds: dict[str, str] | None) -> bool:
    return bool(kinds) and "dictation" in kinds and "shadow" in kinds


def _progress(deps: AppDeps, song_id: int) -> dict:
    new = deps.conn.execute("SELECT id FROM song_chunks WHERE song_id = ? AND repeat_of IS NULL",
                            (song_id,)).fetchall()
    practice = _practice(deps, song_id)
    return {"done": sum(_is_done(practice.get(c["id"])) for c in new), "total": len(new)}


def _summary(deps: AppDeps, row) -> dict:
    progress = _progress(deps, row["id"])
    return {"id": row["id"], "title": row["title"], "artist": row["artist"], "link": row["link"],
            "grammar_status": row["grammar_status"], "is_current": bool(row["is_current"]),
            "total_chunks": progress["total"], "done_chunks": progress["done"]}


def _record(deps: AppDeps, song_id: int, chunk_id: int | None, kind: str, text: str, score: int) -> None:
    insert(deps.conn, "song_practice", song_id=song_id, chunk_id=chunk_id, kind=kind, text=text, score=score,
           day=deps.clock.today().isoformat(), created_at=deps.clock.now().astimezone(timezone.utc).isoformat())


@router.post("/songs")
def create_song(body: SongIn, deps: AppDeps = Depends(get_deps)):
    chunks = split_chunks(body.lyrics)
    if not chunks:
        raise AppError("empty_lyrics", 422, "A letra está vazia.")
    has_current = deps.conn.execute("SELECT 1 FROM songs WHERE is_current = 1").fetchone()
    song_id = insert(deps.conn, "songs", title=body.title.strip(), artist=body.artist.strip(), link=body.link,
                     lyrics=body.lyrics, is_current=0 if has_current else 1,
                     created_at=deps.clock.now().astimezone(timezone.utc).isoformat())
    for c in chunks:
        insert(deps.conn, "song_chunks", song_id=song_id, idx=c.index, text=c.text, repeat_of=c.repeat_of)
    try:
        tag_song(deps, song_id)
    except Exception:  # the song is saved anyway; tagging can be retried
        pass
    return _summary(deps, _song(deps, song_id))


@router.post("/songs/{song_id}/tag")
def retag_song(song_id: int, deps: AppDeps = Depends(get_deps)):
    _song(deps, song_id)
    tag_song(deps, song_id)
    return _summary(deps, _song(deps, song_id))


@router.get("/songs")
def list_songs(deps: AppDeps = Depends(get_deps)):
    rows = deps.conn.execute("SELECT * FROM songs ORDER BY id").fetchall()
    return [_summary(deps, r) for r in rows]


@router.put("/songs/{song_id}/current")
def make_current(song_id: int, deps: AppDeps = Depends(get_deps)):
    _song(deps, song_id)
    deps.conn.execute("UPDATE songs SET is_current = (id = ?)", (song_id,))
    deps.conn.commit()
    return _summary(deps, _song(deps, song_id))


@router.delete("/songs/{song_id}")
def delete_song(song_id: int, deps: AppDeps = Depends(get_deps)):
    _song(deps, song_id)
    deps.conn.execute("DELETE FROM song_practice WHERE song_id = ?", (song_id,))
    deps.conn.execute("DELETE FROM song_chunks WHERE song_id = ?", (song_id,))
    deps.conn.execute("DELETE FROM songs WHERE id = ?", (song_id,))
    deps.conn.commit()
    return {"deleted": song_id}


def _chunk_view(deps: AppDeps, c) -> dict:
    highlights = json.loads(c["highlights"] or "[]")
    titles = []
    for h in highlights:
        try:
            title = deps.content.get(h["module_id"]).title
        except KeyError:
            continue
        if title not in titles:
            titles.append(title)
    return {"id": c["id"], "idx": c["idx"], "text": c["text"], "highlights": highlights, "module_titles": titles}


@router.get("/songs/current/today")
def today(deps: AppDeps = Depends(get_deps)):
    song = deps.conn.execute("SELECT * FROM songs WHERE is_current = 1").fetchone()
    if song is None:
        return {"song": None, "chunk": None, "review_chunks": [], "progress": {"done": 0, "total": 0},
                "stage": "no_song"}
    chunks = deps.conn.execute("SELECT * FROM song_chunks WHERE song_id = ? ORDER BY idx", (song["id"],)).fetchall()
    practice = _practice(deps, song["id"])
    day = deps.clock.today().isoformat()
    new = [c for c in chunks if c["repeat_of"] is None]
    current = next((c for c in new if not _is_done(practice.get(c["id"]))), None)
    completed_today = any(_is_done(practice.get(c["id"])) and max(practice[c["id"]].values()) == day for c in new)
    result = {"song": _summary(deps, song), "chunk": None, "review_chunks": [],
              "progress": _progress(deps, song["id"])}
    if current is None:
        finals = deps.conn.execute("SELECT 1 FROM song_practice WHERE song_id = ? AND kind = 'final'",
                                   (song["id"],)).fetchone()
        return {**result, "stage": "finished" if finals else "final"}
    started_today = any(d == day for d in practice.get(current["id"], {}).values())
    if completed_today and not started_today:
        return {**result, "stage": "done_today"}
    before = [c["idx"] for c in new if c["idx"] < current["idx"]]
    low = before[-1] if before else -1
    review = [c for c in chunks if c["repeat_of"] is not None and low < c["idx"] < current["idx"]]
    stage = "shadow" if "dictation" in practice.get(current["id"], {}) else "dictation"
    return {**result, "chunk": _chunk_view(deps, current), "review_chunks": [_chunk_view(deps, c) for c in review],
            "stage": stage}


@router.post("/songs/chunks/{chunk_id}/dictation")
def dictation(chunk_id: int, body: DictationIn, deps: AppDeps = Depends(get_deps)):
    chunk = _chunk(deps, chunk_id)
    diff = word_diff(chunk["text"], body.text)
    _record(deps, chunk["song_id"], chunk_id, "dictation", body.text, diff["score"])
    return {**diff, "expected": chunk["text"]}


async def _transcribe(deps: AppDeps, audio: UploadFile) -> str:
    data = await audio.read()
    deps.tracker.ensure_can_spend(deps.providers.stt.is_paid)
    result = deps.providers.stt.transcribe(data, audio.content_type or "audio/webm")
    deps.tracker.record(result.usage)
    text = result.text.strip()
    if not heard_words(text):
        raise EmptyTranscript()
    return text


@router.post("/songs/chunks/{chunk_id}/shadow")
async def shadow(chunk_id: int, audio: UploadFile = File(...), deps: AppDeps = Depends(get_deps)):
    chunk = _chunk(deps, chunk_id)
    heard = await _transcribe(deps, audio)
    diff = word_diff(chunk["text"], heard)
    _record(deps, chunk["song_id"], chunk_id, "shadow", heard, diff["score"])
    return {**diff, "heard": heard}


@router.post("/songs/{song_id}/final")
async def final(song_id: int, audio: UploadFile = File(...), deps: AppDeps = Depends(get_deps)):
    song = _song(deps, song_id)
    heard = await _transcribe(deps, audio)
    diff = word_diff(lyrics_text(song["lyrics"]), heard)
    _record(deps, song_id, None, "final", heard, diff["score"])
    return {**diff, "heard": heard}
