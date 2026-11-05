import csv
import io
import json

SENTENCE = "How many people done doubted you"


def ok(translation="já", note="informal, rap"):
    return json.dumps({"translation": translation, "note": note})


def test_translation_is_cached_by_word_and_sentence(app_client, providers):
    providers.chat.responses.append(ok())
    first = app_client.post("/translate", json={"word": "done", "sentence": SENTENCE}).json()
    assert first == {"translation": "já", "note": "informal, rap", "cached": False}
    again = app_client.post("/translate", json={"word": "Done", "sentence": "  how many people done doubted you. "})
    assert again.json() == {"translation": "já", "note": "informal, rap", "cached": True}
    assert len(providers.chat.calls) == 1
    system = providers.chat.calls[0][0]
    assert "done" in system and SENTENCE in system


def test_same_word_in_another_sentence_asks_again(app_client, providers):
    providers.chat.responses.extend([ok(), ok("feito", "")])
    app_client.post("/translate", json={"word": "done", "sentence": SENTENCE})
    other = app_client.post("/translate", json={"word": "done", "sentence": "The cake is done"}).json()
    assert other["translation"] == "feito" and len(providers.chat.calls) == 2


def test_blank_or_long_word_is_rejected(app_client, providers):
    assert app_client.post("/translate", json={"word": "  ", "sentence": "x"}).status_code == 422
    assert app_client.post("/translate", json={"word": "a" * 61, "sentence": "x"}).status_code == 422
    assert providers.chat.calls == []


def test_ai_failure_is_reported_and_not_cached(app_client, providers):
    providers.chat.responses.extend(["bad", "bad"])
    assert app_client.post("/translate", json={"word": "done", "sentence": SENTENCE}).status_code == 502
    providers.chat.responses.append(ok())
    assert app_client.post("/translate", json={"word": "done", "sentence": SENTENCE}).json()["cached"] is False


def test_words_crud(app_client):
    w = app_client.post("/words", json={"word": "grim", "sentence": "a grim night", "translation": "sombrio",
                                        "note": "", "source": "tap"}).json()
    assert app_client.get("/words").json()[0]["word"] == "grim"
    assert app_client.delete(f"/words/{w['id']}").status_code == 200
    assert app_client.get("/words").json() == []
    assert app_client.delete("/words/999").status_code == 404


def test_export_csv_for_anki(app_client):
    app_client.post("/words", json={"word": "grim", "sentence": "a grim night; really", "translation": "sombrio",
                                    "note": "", "source": "tap"})
    app_client.post("/words", json={"word": "done", "sentence": "", "translation": "já", "note": "informal",
                                    "source": "tap"})
    r = app_client.get("/words/export.csv")
    assert r.headers["content-type"].startswith("text/csv")
    rows = list(csv.reader(io.StringIO(r.text), delimiter=";"))
    assert rows == [["grim — a grim night; really", "sombrio"], ["done", "já (informal)"]]
    assert r.text.splitlines()[0].startswith('"grim')  # the field with ";" is quoted
