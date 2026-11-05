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
