"""Regression tests for the findings of the final whole-branch review."""
import pytest

from app.ai.report import finish_session
from app.db import insert
from app.errors import AppError, ProviderAuthFailed, ProviderUnavailable
from app.providers.anthropic_provider import AnthropicText
from app.providers.base import Msg
from app.providers.fakes import FakeTextModel
from app.providers.gemini import GeminiText
from app.providers.local_stt import LocalWhisperStt
from app.sessions_repo import get_session
from builders import add_user_message, make_session, report_json
from sdk_fakes import AuthError, FakeAnthropicClient, FakeGeminiClient, FakeWhisperModel, ServerError

MODULE = "b1_past_simple_continuous"


def count(deps, table, where="1=1"):
    return deps.conn.execute(f"SELECT COUNT(*) FROM {table} WHERE {where}").fetchone()[0]


def turn(app_client, sid, text=None, audio=None):
    data = {"want_audio": "false"}
    if text is not None:
        data["text"] = text
    files = {"audio": ("clip.webm", audio, "audio/webm")} if audio is not None else None
    return app_client.post(f"/sessions/{sid}/turn", data=data, files=files)


# 1. Whisper inventing text from noise ------------------------------------------------------

def test_local_stt_drops_segments_that_are_probably_not_speech():
    model = FakeWhisperModel(texts=("Thank you.", " Hello"), no_speech=[0.9, 0.05])
    assert LocalWhisperStt(decode=lambda b: b, model=model).transcribe(b"x", "audio/wav").text == "Hello"


def test_local_stt_asks_the_model_to_filter_silence():
    model = FakeWhisperModel()
    LocalWhisperStt(decode=lambda b: b, model=model).transcribe(b"x", "audio/wav")
    assert model.calls[0]["vad_filter"] is True


@pytest.mark.parametrize("heard", ["...", "♪ ♪", "  -  ", "123"])
def test_transcript_without_letters_counts_as_nothing_heard(app_client, deps, providers, heard):
    providers.stt.text = heard
    sid = make_session(deps)
    r = turn(app_client, sid, audio=b"noise")
    assert r.status_code == 422 and r.json()["error"] == "empty_transcript"
    assert providers.chat.calls == [] and count(deps, "messages") == 0


def test_stt_route_also_ignores_lettersless_text(app_client, providers):
    providers.stt.text = "..."
    r = app_client.post("/stt", files={"audio": ("c.webm", b"x", "audio/webm")})
    assert r.status_code == 422


# 2. Pull-forward must not cancel the schedule of the module just studied -------------------

def test_a_module_session_keeps_its_own_spaced_repetition_schedule(app_client, deps, providers):
    insert(deps.conn, "reviews", module_id=MODULE, next_due="2026-11-03", interval_days=3, ease=2.5, repetitions=1)
    sid = make_session(deps, kind="review")
    add_user_message(deps, sid)
    mistakes = [{"said": f"bad {i}", "corrected": "ok", "explanation": "e", "module_id": MODULE} for i in range(3)]
    providers.report.responses.append(report_json(90, mistakes))
    body = app_client.post(f"/sessions/{sid}/finish").json()
    stored = deps.conn.execute("SELECT next_due FROM reviews WHERE module_id = ?", (MODULE,)).fetchone()[0]
    assert body["next_due"] is None and stored == "2026-11-03"  # reviews are scheduled by the exercise bank


# 4. Provider failures ----------------------------------------------------------------------

def test_gemini_retries_a_server_error_once_then_succeeds():
    client = FakeGeminiClient("ok", errors=[ServerError("503 overloaded")])
    sleeps = []
    model = GeminiText("k", "m", client=client, sleep=sleeps.append, retry_wait=1.0)
    assert model.generate("s", [Msg("user", "x")]).text == "ok" and sleeps == [1.0]


def test_gemini_server_errors_twice_become_provider_unavailable():
    client = FakeGeminiClient(errors=[ServerError("503"), ServerError("503")])
    model = GeminiText("k", "m", client=client, sleep=lambda s: None)
    with pytest.raises(ProviderUnavailable) as exc:
        model.generate("s", [Msg("user", "x")])
    assert exc.value.code == "provider_unavailable" and exc.value.extra["provider"] == "gemini"


def test_gemini_bad_key_is_reported_as_auth_failure_without_retry():
    client = FakeGeminiClient(errors=[AuthError("API key not valid")])
    with pytest.raises(ProviderAuthFailed):
        GeminiText("k", "m", client=client, sleep=lambda s: None).generate("s", [Msg("user", "x")])
    assert len(client.calls) == 1


def test_anthropic_overloaded_and_auth_errors_are_mapped():
    class Overloaded(Exception):
        status_code = 529

    with pytest.raises(ProviderUnavailable):
        AnthropicText("k", "m", client=FakeAnthropicClient(errors=[Overloaded("overloaded")])).generate(
            "s", [Msg("user", "x")])
    with pytest.raises(ProviderAuthFailed):
        AnthropicText("k", "m", client=FakeAnthropicClient(errors=[AuthError("invalid x-api-key")])).generate(
            "s", [Msg("user", "x")])


def test_unexpected_server_errors_still_carry_cors_headers(app_client):
    def boom():
        raise RuntimeError("unexpected")

    app_client.app.add_api_route("/boom-unexpected", boom)
    r = app_client.get("/boom-unexpected", headers={"Origin": "http://localhost:8081"})
    assert r.status_code == 500 and r.json()["error"] == "internal_error"
    assert "access-control-allow-origin" in r.headers


# 5. Finishing: no double work when two requests overlap, and a failed finish can be retried --

def test_overlapping_finish_requests_do_the_work_once(app_client, deps, providers):
    sid = make_session(deps)
    add_user_message(deps, sid)
    outcomes = []

    class Reentrant(FakeTextModel):
        def generate(self, *args, **kwargs):
            try:
                finish_session(deps, get_session(deps.conn, sid))
                outcomes.append("ran twice")
            except AppError as e:
                outcomes.append(e.code)
            return super().generate(*args, **kwargs)

    providers.report = Reentrant([report_json(90)])
    deps.providers.report = providers.report
    assert app_client.post(f"/sessions/{sid}/finish").status_code == 200
    assert outcomes == ["finish_in_progress"]
    assert len(providers.report.calls) == 1 and count(deps, "reviews") == 0


def test_a_failed_finish_can_be_retried(app_client, deps, providers):
    sid = make_session(deps)
    add_user_message(deps, sid)
    providers.report.responses.extend(["bad", "bad again"])
    assert app_client.post(f"/sessions/{sid}/finish").status_code == 502
    providers.report.responses.append(report_json(80))
    retry = app_client.post(f"/sessions/{sid}/finish")
    assert retry.status_code == 200 and retry.json()["conversation_score"] == 80
    assert deps.conn.execute("SELECT is_finished FROM sessions WHERE id = ?", (sid,)).fetchone()[0] == 1


# 6. A failed turn must not leave the learner's line behind ---------------------------------

def test_failed_turn_saves_nothing_so_a_resend_is_not_duplicated(app_client, deps, providers):
    sid = make_session(deps)

    def fail(*args, **kwargs):
        raise RuntimeError("provider down")

    original = providers.chat.generate
    providers.chat.generate = fail
    assert turn(app_client, sid, text="I went home").status_code == 500
    assert count(deps, "messages") == 0

    providers.chat.generate = original
    providers.chat.responses.append("Nice!")
    assert turn(app_client, sid, text="I went home").status_code == 200
    assert count(deps, "messages", "role = 'user'") == 1


# 7. The history sent to the model must start with a user message ---------------------------

def test_history_after_the_ai_opening_starts_with_a_user_message(app_client, deps, providers):
    sid = make_session(deps)
    providers.chat.responses.extend(["Hi there! What can I get you?", "Sure, anything else?"])
    assert turn(app_client, sid).status_code == 200  # the AI opens
    assert turn(app_client, sid, text="A coffee, please.").status_code == 200
    sent = providers.chat.calls[1][1]
    assert sent[0].role == "user" and sent[-1].content == "A coffee, please."
    assert [m.role for m in sent] == ["user", "assistant", "user"]
