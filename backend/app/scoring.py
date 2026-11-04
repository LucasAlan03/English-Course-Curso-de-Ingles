def final_score(listening_pct: float | None, conversation: int) -> int:
    """40% listening + 60% conversation; conversation only when there was no listening."""
    if listening_pct is None:
        return conversation
    return round(0.4 * listening_pct + 0.6 * conversation)
