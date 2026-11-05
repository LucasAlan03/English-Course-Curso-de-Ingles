"""Answer normalization and grading for hand-written exercises (no AI)."""

import re
import unicodedata

_QUOTES = str.maketrans({"‘": "'", "’": "'", "ʼ": "'", "`": "'", "“": '"', "”": '"'})
_CONTRACTIONS = [
    (re.compile(r"\bwon't\b"), "will not"),
    (re.compile(r"\bcan't\b"), "can not"),
    (re.compile(r"\bcannot\b"), "can not"),
    (re.compile(r"n't\b"), " not"),
    (re.compile(r"'m\b"), " am"),
    (re.compile(r"'re\b"), " are"),
    (re.compile(r"'ve\b"), " have"),
    (re.compile(r"'ll\b"), " will"),
]


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).translate(_QUOTES).lower()
    text = text.replace(",", " ").replace('"', " ")
    text = text.strip(" .!?;:\t\n\r")
    text = re.sub(r"\s+", " ", text)
    for pattern, replacement in _CONTRACTIONS:
        text = pattern.sub(replacement, text)
    return re.sub(r"\s+", " ", text).strip()


def is_correct(exercise, answer: str) -> bool:
    given = normalize(answer)
    return any(given == normalize(a) for a in exercise.answers)


def pick_review(conn, module_id: str, exercises: list, size: int = 9) -> list:
    """Missed exercises first (newest mistake first), then the ones seen longest ago."""
    latest: dict[str, tuple[str, int]] = {}
    rows = conn.execute(
        "SELECT exercise_id, correct, created_at FROM exercise_attempts WHERE module_id = ? ORDER BY created_at, id",
        (module_id,),
    ).fetchall()
    for r in rows:
        latest[r["exercise_id"]] = (r["created_at"], r["correct"])
    missed = [e for e in exercises if e.id in latest and not latest[e.id][1]]
    missed.sort(key=lambda e: e.id)
    missed.sort(key=lambda e: latest[e.id][0], reverse=True)  # stable: ties keep id order
    rest = [e for e in exercises if not (e.id in latest and not latest[e.id][1])]
    rest.sort(key=lambda e: (latest[e.id][0] if e.id in latest else "", e.id))
    return (missed + rest)[:size]
