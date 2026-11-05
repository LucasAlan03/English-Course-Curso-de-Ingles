import json
from datetime import datetime, timezone

from app.clock import FixedClock

# Invented lines only: real lyrics never go into tracked files.
LYRICS = "[Verse]\nI was walking home\nwhen the rain began\n\nwe sing it loud\nwe sing it proud\n\n" \
         "(Chorus)\nI was walking home\nwhen the rain began\n\nif I had a car\nI would drive away\n"
# chunks: 0 new, 1 new, 2 repeat of 0, 3 new


def grammar_json(highlights):
    return json.dumps({"chunks": highlights})


def create(app_client, providers, highlights=None, **overrides):
    providers.report.responses.append(grammar_json(highlights or []))
    body = {"title": "Rain Song", "artist": "Nobody", "link": "https://youtu.be/abcdefgh", "lyrics": LYRICS}
    return app_client.post("/songs", json={**body, **overrides})


def test_create_song_stores_chunks_and_becomes_current(app_client, providers, deps):
    r = create(app_client, providers)
    assert r.status_code == 200
    body = r.json()
    assert body["total_chunks"] == 3 and body["grammar_status"] == "done" and "lyrics" not in body
    assert deps.conn.execute("SELECT COUNT(*) FROM song_chunks").fetchone()[0] == 4
    listed = app_client.get("/songs").json()
    assert listed[0]["is_current"] is True and listed[0]["done_chunks"] == 0
    assert "lyrics" not in listed[0] and "walking" not in json.dumps(listed)


def test_empty_lyrics_are_rejected(app_client, providers):
    r = app_client.post("/songs", json={"title": "x", "artist": "y", "lyrics": "\n[Chorus]\n\n"})
    assert r.status_code == 422 and r.json()["error"] == "empty_lyrics"
    assert providers.report.calls == []


def test_ai_failure_keeps_the_song_pending_and_retry_tags_it(app_client, providers, deps):
    providers.report.responses.extend(["bad", "still bad"])
    r = app_client.post("/songs", json={"title": "x", "artist": "y", "lyrics": LYRICS})
    assert r.status_code == 200 and r.json()["grammar_status"] == "pending"
    providers.report.responses.append(grammar_json([]))
    assert app_client.post(f"/songs/{r.json()['id']}/tag").json()["grammar_status"] == "done"


def test_tagging_keeps_only_valid_highlights(app_client, providers, deps):
    create(app_client, providers, highlights=[
        {"index": 0, "highlights": [
            {"phrase": "I was walking", "module_id": "b1_past_simple_continuous"},
            {"phrase": "not in this chunk", "module_id": "b1_past_simple_continuous"},
            {"phrase": "the rain began", "module_id": "unknown_module"}]},
        {"index": 3, "highlights": [{"phrase": "if I had a car", "module_id": "b1_futures"}]},
    ])
    rows = deps.conn.execute("SELECT idx, highlights FROM song_chunks ORDER BY idx").fetchall()
    assert json.loads(rows[0]["highlights"]) == [{"phrase": "I was walking", "module_id": "b1_past_simple_continuous"}]
    assert json.loads(rows[3]["highlights"]) == [{"phrase": "if I had a car", "module_id": "b1_futures"}]
    assert json.loads(rows[1]["highlights"]) == []


def today(app_client):
    return app_client.get("/songs/current/today").json()


def practice(app_client, providers, chunk, sung=None):
    app_client.post(f"/songs/chunks/{chunk['id']}/dictation", json={"text": chunk["text"]})
    providers.stt.text = sung or chunk["text"]
    return app_client.post(f"/songs/chunks/{chunk['id']}/shadow", files={"audio": ("a.webm", b"x", "audio/webm")})


def next_day(deps, day):
    deps.clock = FixedClock(datetime(2026, 11, day, 15, 0, tzinfo=timezone.utc), "America/Sao_Paulo")


def test_no_song_stage(app_client):
    assert today(app_client)["stage"] == "no_song"


def test_today_chunk_advances_only_after_dictation_and_shadow(app_client, providers, deps):
    create(app_client, providers, highlights=[
        {"index": 0, "highlights": [{"phrase": "I was walking", "module_id": "b1_past_simple_continuous"}]}])
    t = today(app_client)
    assert t["stage"] == "dictation" and t["chunk"]["idx"] == 0
    assert t["chunk"]["module_titles"] == ["Past simple x past continuous"]
    d = app_client.post(f"/songs/chunks/{t['chunk']['id']}/dictation", json={"text": "I was walking home"}).json()
    assert d["score"] == 50 and today(app_client)["stage"] == "shadow"
    providers.stt.text = "I was walking home when the rain began"
    s = app_client.post(f"/songs/chunks/{t['chunk']['id']}/shadow", files={"audio": ("a.webm", b"x", "audio/webm")})
    assert s.json()["score"] == 100
    t = today(app_client)
    assert t["stage"] == "done_today" and t["progress"] == {"done": 1, "total": 3}
    next_day(deps, 4)
    t = today(app_client)
    assert t["stage"] == "dictation" and t["chunk"]["idx"] == 1


def test_repeat_chunk_is_only_a_quick_review(app_client, providers, deps):
    create(app_client, providers)
    for day in (3, 4):
        next_day(deps, day)
        practice(app_client, providers, today(app_client)["chunk"])
    next_day(deps, 5)
    t = today(app_client)
    assert t["chunk"]["idx"] == 3
    assert [c["idx"] for c in t["review_chunks"]] == [2]


def test_final_stage_after_the_last_chunk_then_finished(app_client, providers, deps):
    r = create(app_client, providers)
    for day in (3, 4, 5):
        next_day(deps, day)
        practice(app_client, providers, today(app_client)["chunk"])
    next_day(deps, 6)
    assert today(app_client)["stage"] == "final"
    providers.stt.text = "I was walking home when the rain began"
    f = app_client.post(f"/songs/{r.json()['id']}/final", files={"audio": ("a.webm", b"x", "audio/webm")}).json()
    assert 0 < f["score"] < 100
    assert today(app_client)["stage"] == "finished"


def test_silent_shadow_is_an_error_and_not_stored(app_client, providers, deps):
    create(app_client, providers)
    chunk = today(app_client)["chunk"]
    r = practice(app_client, providers, chunk, sung="...")
    assert r.status_code == 422
    assert deps.conn.execute("SELECT COUNT(*) FROM song_practice WHERE kind = 'shadow'").fetchone()[0] == 0


def test_switch_current_song_and_delete(app_client, providers):
    first = create(app_client, providers).json()
    second = create(app_client, providers, title="Other").json()
    assert {s["id"]: s["is_current"] for s in app_client.get("/songs").json()} == {first["id"]: True,
                                                                                  second["id"]: False}
    app_client.put(f"/songs/{second['id']}/current")
    assert today(app_client)["song"]["id"] == second["id"]
    assert app_client.delete(f"/songs/{second['id']}").status_code == 200
    assert [s["id"] for s in app_client.get("/songs").json()] == [first["id"]]
    assert app_client.put("/songs/999/current").status_code == 404
