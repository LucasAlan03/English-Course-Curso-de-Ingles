import os

from builders import listening_json, make_session
from app.db import insert


def count(deps, table):
    return deps.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def get_items(app_client, deps, providers, kind="lesson", n=5):
    providers.report.responses.append(listening_json(n))
    sid = make_session(deps, kind=kind)
    r = app_client.get(f"/sessions/{sid}/listening")
    assert r.status_code == 200, r.text
    return sid, r.json()


def test_generate_listening_creates_5_items_with_audio(app_client, deps, providers):
    sid, items = get_items(app_client, deps, providers)
    assert len(items) == 5
    assert [i["kind"] for i in items].count("choice") == 3
    audio_dir = os.path.join(deps.settings.data_dir, "audio")
    assert len(os.listdir(audio_dir)) == 5
    audio = app_client.get(items[0]["audio_url"])
    assert audio.status_code == 200 and audio.content == b"FAKEAUDIO"


def test_listing_hides_answers(app_client, deps, providers):
    _, items = get_items(app_client, deps, providers)
    for item in items:
        assert "answer" not in item and "explanation" not in item
        assert {"id", "kind", "prompt", "audio_url"} <= set(item)
    assert items[0]["options"] == ["went", "go", "gone"]
    assert items[-1]["options"] is None


def test_review_session_generates_3_items(app_client, deps, providers):
    _, items = get_items(app_client, deps, providers, kind="review", n=3)
    assert len(items) == 3
    system_prompt = providers.report.calls[0][0]
    assert "3 listening exercises" in system_prompt


def test_second_get_does_not_regenerate(app_client, deps, providers):
    sid, first = get_items(app_client, deps, providers)
    again = app_client.get(f"/sessions/{sid}/listening").json()
    assert [i["id"] for i in again] == [i["id"] for i in first]
    assert len(providers.report.calls) == 1


def test_answer_choice_correct_and_wrong(app_client, deps, providers):
    _, items = get_items(app_client, deps, providers)
    ok = app_client.post(f"/listening/{items[0]['id']}/answer", json={"answer": "went"}).json()
    assert ok == {"correct": True, "correct_answer": "went", "explanation": "Past simple."}
    bad = app_client.post(f"/listening/{items[1]['id']}/answer", json={"answer": "gone"}).json()
    assert bad["correct"] is False and bad["correct_answer"] == "went"


def test_answering_twice_keeps_the_first_answer(app_client, deps, providers):
    _, items = get_items(app_client, deps, providers)
    url = f"/listening/{items[0]['id']}/answer"
    assert app_client.post(url, json={"answer": "gone"}).json()["correct"] is False
    assert app_client.post(url, json={"answer": "went"}).json()["correct"] is False


def test_gap_answer_ignores_case_and_punctuation(app_client, deps, providers):
    _, items = get_items(app_client, deps, providers)
    gap = next(i for i in items if i["kind"] == "gap")
    assert app_client.post(f"/listening/{gap['id']}/answer", json={"answer": "  Went. "}).json()["correct"] is True


def test_recent_mistakes_included_in_prompt(app_client, deps, providers):
    old = make_session(deps)
    insert(deps.conn, "mistakes", session_id=old, module_id="b1_past_simple_continuous",
           said="I goed to school", corrected="I went to school", explanation="irregular", created_at="x")
    get_items(app_client, deps, providers)
    assert "I goed to school" in providers.report.calls[0][0]


def test_invalid_ai_output_saves_nothing(app_client, deps, providers):
    providers.report.responses.extend(["not json", "still not json"])
    sid = make_session(deps)
    r = app_client.get(f"/sessions/{sid}/listening")
    assert r.status_code == 502 and r.json()["error"] == "invalid_ai_output"
    assert count(deps, "listening_items") == 0


def test_wrong_item_count_from_ai_is_rejected(app_client, deps, providers):
    providers.report.responses.append(listening_json(3))  # a lesson needs 5
    sid = make_session(deps)
    r = app_client.get(f"/sessions/{sid}/listening")
    assert r.status_code == 502 and count(deps, "listening_items") == 0


def test_usage_is_recorded_for_text_and_audio(app_client, deps, providers):
    get_items(app_client, deps, providers)
    assert count(deps, "api_usage") == 1 + 5


def test_unknown_session_404_and_free_session_400(app_client, deps):
    assert app_client.get("/sessions/999/listening").status_code == 404
    free = make_session(deps, kind="free", module_id=None)
    assert app_client.get(f"/sessions/{free}/listening").status_code == 400


def test_audio_rejects_unsafe_names(app_client):
    assert app_client.get("/audio/evil.txt").status_code == 404
    assert app_client.get("/audio/missing.wav").status_code == 404


def test_audio_accepts_query_token_but_not_a_wrong_one(app_client, deps, providers):
    _, items = get_items(app_client, deps, providers)
    url = items[0]["audio_url"]
    no_header = {"X-API-Token": ""}
    assert app_client.get(f"{url}?token=test-token", headers=no_header).status_code == 200
    assert app_client.get(f"{url}?token=wrong", headers=no_header).status_code == 401
    assert app_client.get(url, headers=no_header).status_code == 401
