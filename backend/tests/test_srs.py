from datetime import date, timedelta

from app.srs import ReviewState, next_state

TODAY = date(2026, 11, 3)


def st(interval, ease, reps):
    return ReviewState(interval, ease, reps, TODAY)


def test_lesson_starts_with_one_day_interval():
    s = next_state(None, 90, TODAY)
    assert (s.interval_days, s.ease, s.repetitions) == (1, 2.5, 0)
    assert s.next_due == TODAY + timedelta(days=1)


def test_lesson_low_score_still_one_day():
    s = next_state(None, 40, TODAY)
    assert (s.interval_days, s.ease, s.repetitions) == (1, 2.5, 0)


def test_first_review_good_goes_to_three_days():
    s = next_state(st(1, 2.5, 0), 90, TODAY)
    assert (s.interval_days, s.ease, s.repetitions) == (3, 2.6, 1)
    assert s.next_due == TODAY + timedelta(days=3)


def test_first_review_medium_goes_to_three_days_ease_unchanged():
    s = next_state(st(1, 2.5, 0), 70, TODAY)
    assert (s.interval_days, s.ease, s.repetitions) == (3, 2.5, 1)


def test_good_score_multiplies_by_ease_and_raises_ease():
    s = next_state(st(3, 2.5, 1), 90, TODAY)
    assert (s.interval_days, s.ease, s.repetitions) == (8, 2.6, 2)  # 3 * 2.5 = 7.5 -> 8


def test_medium_score_grows_by_1_2():
    s = next_state(st(8, 2.6, 2), 70, TODAY)
    assert (s.interval_days, s.ease, s.repetitions) == (10, 2.6, 3)  # 9.6 -> 10


def test_low_score_resets_to_tomorrow_and_lowers_ease():
    s = next_state(st(8, 2.6, 2), 50, TODAY)
    assert (s.interval_days, s.ease, s.repetitions) == (1, 2.4, 0)
    assert s.next_due == TODAY + timedelta(days=1)


def test_ease_is_clamped():
    assert next_state(st(8, 3.0, 2), 95, TODAY).ease == 3.0
    assert next_state(st(8, 1.3, 2), 10, TODAY).ease == 1.3
