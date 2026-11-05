"""Marks, once per song, the phrases that use the grammar of a course module."""

import json

from app.ai.prompts import render
from app.ai.schemas import SongGrammar
from app.ai.structured import generate_structured
from app.deps import AppDeps
from app.providers.base import Msg
from app.songs import words


def _contains(chunk_text: str, phrase: str) -> bool:
    needle, hay = words(phrase), words(chunk_text)
    return bool(needle) and any(hay[i:i + len(needle)] == needle for i in range(len(hay) - len(needle) + 1))


def tag_song(deps: AppDeps, song_id: int) -> None:
    chunks = deps.conn.execute("SELECT id, idx, text FROM song_chunks WHERE song_id = ? AND repeat_of IS NULL "
                               "ORDER BY idx", (song_id,)).fetchall()
    known = {m.id: m for m in deps.content.all()}
    system = render("song_grammar", deps.settings.prompts_dir,
                    modules="\n".join(f"{m.id}: {m.title}" for m in known.values()),
                    chunks="\n\n".join(f"[{c['idx']}]\n{c['text']}" for c in chunks))
    result = generate_structured(deps.providers.report, system, [Msg("user", "Mark the grammar now.")],
                                 SongGrammar, deps.tracker)
    by_idx = {c["idx"]: c for c in chunks}
    kept: dict[int, list[dict]] = {}
    for item in result.chunks:
        chunk = by_idx.get(item.index)
        if chunk is None:
            continue
        for h in item.highlights:
            if h.module_id in known and _contains(chunk["text"], h.phrase):
                kept.setdefault(chunk["idx"], []).append({"phrase": h.phrase, "module_id": h.module_id})
    for c in chunks:
        deps.conn.execute("UPDATE song_chunks SET highlights = ? WHERE id = ?", (json.dumps(kept.get(c["idx"], [])), c["id"]))
    deps.conn.execute("UPDATE song_chunks SET highlights = (SELECT o.highlights FROM song_chunks o "
                      "WHERE o.song_id = song_chunks.song_id AND o.idx = song_chunks.repeat_of) "
                      "WHERE song_id = ? AND repeat_of IS NOT NULL", (song_id,))
    deps.conn.execute("UPDATE songs SET grammar_status = 'done' WHERE id = ?", (song_id,))
    deps.conn.commit()
