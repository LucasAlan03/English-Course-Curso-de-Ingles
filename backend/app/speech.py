import re


def heard_words(text: str) -> bool:
    """False for empty or lettersless transcripts such as "...", "♪" or "123"."""
    return bool(re.search(r"[A-Za-z]", text))
