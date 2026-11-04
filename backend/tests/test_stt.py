def post_audio(app_client, data=b"fake-audio"):
    return app_client.post("/stt", files={"audio": ("clip.webm", data, "audio/webm")})


def test_stt_returns_text(app_client, providers):
    providers.stt.text = "Hello, this is a test."
    r = post_audio(app_client)
    assert r.status_code == 200 and r.json() == {"text": "Hello, this is a test."}


def test_stt_empty_returns_422(app_client, providers):
    providers.stt.text = "  "
    r = post_audio(app_client)
    assert r.status_code == 422 and r.json()["error"] == "empty_transcript"


def test_stt_records_usage(app_client, deps):
    post_audio(app_client)
    assert deps.conn.execute("SELECT COUNT(*) FROM api_usage WHERE kind = 'stt'").fetchone()[0] == 1
