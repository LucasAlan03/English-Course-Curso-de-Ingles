"""Song lyrics: split into practice chunks and compare what the learner heard or sang."""

import re
from dataclasses import dataclass
from difflib import SequenceMatcher

from app.exercises import normalize

_LABEL = re.compile(r"^\s*[\[(].*[\])]\s*$")


@dataclass
class Chunk:
    index: int
    text: str
    repeat_of: int | None


def words(text: str) -> list[str]:
    """Lowercase words without punctuation, contractions expanded like the exercises."""
    return re.findall(r"[a-z0-9']+", normalize(text))


def _stanzas(lyrics: str) -> list[list[str]]:
    stanzas: list[list[str]] = [[]]
    for raw in lyrics.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = raw.strip()
        if _LABEL.match(line):
            continue
        if line:
            stanzas[-1].append(line)
        elif stanzas[-1]:
            stanzas.append([])
    return [s for s in stanzas if s]


def _balanced(lines: list[str], max_lines: int) -> list[list[str]]:
    pieces = -(-len(lines) // max_lines)
    base, extra = divmod(len(lines), pieces)
    out, start = [], 0
    for i in range(pieces):
        size = base + (1 if i < extra else 0)
        out.append(lines[start:start + size])
        start += size
    return out


def split_chunks(lyrics: str, max_lines: int = 4) -> list[Chunk]:
    chunks: list[Chunk] = []
    seen: dict[tuple[str, ...], int] = {}
    for stanza in _stanzas(lyrics):
        for piece in _balanced(stanza, max_lines):
            key = tuple(words(" ".join(piece)))
            index = len(chunks)
            chunks.append(Chunk(index, "\n".join(piece), seen.get(key)))
            seen.setdefault(key, index)
    return chunks


def lyrics_text(lyrics: str) -> str:
    """The whole song without section labels, for the final challenge."""
    return "\n".join("\n".join(s) for s in _stanzas(lyrics))


def word_diff(expected: str, got: str) -> dict:
    exp, have = words(expected), words(got)
    tokens: list[dict] = []
    for op, a1, a2, b1, b2 in SequenceMatcher(a=exp, b=have, autojunk=False).get_opcodes():
        if op == "equal":
            tokens += [{"word": w, "status": "ok"} for w in exp[a1:a2]]
        elif op == "delete":
            tokens += [{"word": w, "status": "missing"} for w in exp[a1:a2]]
        elif op == "replace":
            tokens += [{"word": w, "status": "wrong"} for w in exp[a1:a2]]
        else:
            tokens += [{"word": w, "status": "extra"} for w in have[b1:b2]]
    ok = sum(t["status"] == "ok" for t in tokens)
    return {"score": round(100 * ok / len(exp)) if exp else 0, "tokens": tokens}
