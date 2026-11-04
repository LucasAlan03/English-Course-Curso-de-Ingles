"""Lessons work like a book: their listening exercises are made once and reused. Reviews stay fresh."""
import pytest

from app.ai.listening import ensure_lesson_bank, load_bank
from app.ai.prefill import prefill_lesson_bank
from app.db import insert
from app.errors import ProviderRateLimited
from builders import listening_json, make_session

MODULE = "b1_past_simple_continuous"


def count(deps, table, where="1=1"):
    return deps.conn.execute(f"SELECT COUNT(*) FROM {table} WHERE {where}").fetchone()[0]


def open_lesson(app_client, deps):
    sid = make_session(deps, kind="lesson")
    r = app_client.get(f"/sessions/{sid}/listening")
    assert r.status_code == 200, r.text
    return sid, r.json()


def test_a_lesson_is_generated_once_and_reused_by_later_sessions(app_client, deps, providers):
    providers.report.responses.append(listening_json(5))
    _, first = open_lesson(app_client, deps)
    _, second = open_lesson(app_client, deps)
    assert len(providers.report.calls) == 1  # the AI ran only for the very first opening
    assert [i["audio_url"] for i in first] == [i["audio_url"] for i in second]
    assert [i["prompt"] for i in first] == [i["prompt"] for i in second]
    assert count(deps, "listening_items") == 10  # each session still gets its own rows (own answers)


def test_each_session_keeps_its_own_answers(app_client, deps, providers):
    providers.report.responses.append(listening_json(5))
    _, first = open_lesson(app_client, deps)
    _, second = open_lesson(app_client, deps)
    app_client.post(f"/listening/{first[0]['id']}/answer", json={"answer": "gone"})
    again = app_client.post(f"/listening/{second[0]['id']}/answer", json={"answer": "went"}).json()
    assert again["correct"] is True  # the first session's wrong answer did not leak


def test_the_bank_works_even_when_the_ai_is_unavailable(app_client, deps, providers):
    providers.report.responses.append(listening_json(5))
    open_lesson(app_client, deps)
    providers.report.responses.clear()  # any further AI call would fail the fake
    _, items = open_lesson(app_client, deps)
    assert len(items) == 5


def test_the_bank_is_generic_and_ignores_personal_mistakes(app_client, deps, providers):
    old = make_session(deps)
    insert(deps.conn, "mistakes", session_id=old, module_id=MODULE, said="I goed to school",
           corrected="I went to school", explanation="irregular", created_at="x")
    providers.report.responses.append(listening_json(5))
    open_lesson(app_client, deps)
    assert "I goed to school" not in providers.report.calls[0][0]


def test_reviews_never_use_the_bank_and_stay_personal(app_client, deps, providers):
    providers.report.responses.append(listening_json(5))
    open_lesson(app_client, deps)  # fills the bank
    old = make_session(deps)
    insert(deps.conn, "mistakes", session_id=old, module_id=MODULE, said="I goed to school",
           corrected="I went to school", explanation="irregular", created_at="x")
    providers.report.responses.append(listening_json(3))
    sid = make_session(deps, kind="review")
    items = app_client.get(f"/sessions/{sid}/listening").json()
    assert len(items) == 3 and len(providers.report.calls) == 2
    assert "I goed to school" in providers.report.calls[1][0]


def test_ensure_lesson_bank_is_idempotent(deps, providers):
    providers.report.responses.append(listening_json(5))
    assert ensure_lesson_bank(deps, MODULE) is True
    assert ensure_lesson_bank(deps, MODULE) is False
    bank = load_bank(deps.conn, MODULE)
    assert len(bank) == 5 and all(item["audio_path"].endswith(".wav") for item in bank)
    assert len(providers.report.calls) == 1


def test_invalid_ai_output_does_not_fill_the_bank(app_client, deps, providers):
    providers.report.responses.extend(["bad", "bad again"])
    sid = make_session(deps, kind="lesson")
    assert app_client.get(f"/sessions/{sid}/listening").status_code == 502
    assert load_bank(deps.conn, MODULE) is None and count(deps, "listening_items") == 0


# ---- prefill script logic ----------------------------------------------------------------------

def test_prefill_generates_missing_modules_and_skips_existing(deps, providers):
    providers.report.responses.extend([listening_json(5)] * 3)  # one for the pre-made module, two for the prefill
    ids = ["b1_past_simple_continuous", "b1_futures", "b2_passive_voice"]
    ensure_lesson_bank(deps, "b1_futures")  # already there
    result = prefill_lesson_bank(deps, ids, sleep=lambda s: None, log=lambda m: None)
    assert result == {"done": ["b1_past_simple_continuous", "b2_passive_voice"], "skipped": ["b1_futures"], "failed": []}


def test_prefill_waits_and_retries_when_the_provider_is_rate_limited(deps, providers):
    original = providers.report.generate
    state = {"calls": 0}

    def flaky(*args, **kwargs):
        state["calls"] += 1
        if state["calls"] == 1:
            raise ProviderRateLimited("gemini")
        return original(*args, **kwargs)

    providers.report.generate = flaky
    providers.report.responses.append(listening_json(5))
    waits = []
    result = prefill_lesson_bank(deps, [MODULE], sleep=waits.append, wait_s=30, log=lambda m: None)
    assert result["done"] == [MODULE] and waits == [30]


def test_prefill_gives_up_after_too_many_waits(deps, providers):
    def always_limited(*args, **kwargs):
        raise ProviderRateLimited("gemini")

    providers.report.generate = always_limited
    waits = []
    result = prefill_lesson_bank(deps, [MODULE, "b1_futures"], sleep=waits.append, wait_s=1, max_waits=3,
                                 log=lambda m: None)
    assert result["done"] == [] and result["failed"] == [MODULE, "b1_futures"] and len(waits) == 3
