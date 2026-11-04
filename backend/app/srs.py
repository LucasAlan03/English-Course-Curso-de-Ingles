import math
from dataclasses import dataclass
from datetime import date, timedelta

INITIAL_EASE = 2.5
MIN_EASE = 1.3
MAX_EASE = 3.0


@dataclass(frozen=True)
class ReviewState:
    interval_days: int
    ease: float
    repetitions: int
    next_due: date


def _round_half_up(x: float) -> int:
    return math.floor(x + 0.5)


def _clamp_ease(ease: float) -> float:
    return round(min(MAX_EASE, max(MIN_EASE, ease)), 2)


def next_state(prev: ReviewState | None, score: int, today: date) -> ReviewState:
    """Schedule the next review of a module after a lesson (prev=None) or a review."""
    if prev is None:
        return ReviewState(1, INITIAL_EASE, 0, today + timedelta(days=1))

    if score >= 85:
        ease = _clamp_ease(prev.ease + 0.1)
        factor = prev.ease
    elif score >= 60:
        ease = _clamp_ease(prev.ease)
        factor = 1.2
    else:
        ease = _clamp_ease(prev.ease - 0.2)
        return ReviewState(1, ease, 0, today + timedelta(days=1))

    if prev.repetitions == 0:
        interval = 3
    else:
        interval = _round_half_up(prev.interval_days * factor)
    return ReviewState(interval, ease, prev.repetitions + 1, today + timedelta(days=interval))
