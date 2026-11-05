"""Tap-to-translate: one word in the context of its sentence, cached so a second tap is free."""

from datetime import timezone

from app.ai.prompts import render
from app.ai.schemas import Translation
from app.ai.structured import generate_structured
from app.deps import AppDeps
from app.exercises import normalize
from app.providers.base import Msg


def cache_key(word: str, sentence: str) -> str:
    return normalize(word) + "|" + normalize(sentence)


def translate(deps: AppDeps, word: str, sentence: str) -> dict:
    key = cache_key(word, sentence)
    row = deps.conn.execute("SELECT translation, note FROM translations WHERE key = ?", (key,)).fetchone()
    if row:
        return {"translation": row["translation"], "note": row["note"], "cached": True}
    system = render("translate", deps.settings.prompts_dir, word=word.strip(), sentence=sentence.strip())
    result = generate_structured(deps.providers.chat, system, [Msg("user", "Translate now.")], Translation,
                                 deps.tracker)
    deps.conn.execute(
        "INSERT OR REPLACE INTO translations (key, translation, note, created_at) VALUES (?, ?, ?, ?)",
        (key, result.translation, result.note, deps.clock.now().astimezone(timezone.utc).isoformat()),
    )
    deps.conn.commit()
    return {"translation": result.translation, "note": result.note, "cached": False}
