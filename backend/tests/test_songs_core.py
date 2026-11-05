from app.songs import split_chunks, word_diff

# Invented lines only: real lyrics never go into tracked files.
LYRICS = ("[Intro]\r\nline one\r\nline two\r\n\r\n\r\nchorus a\nchorus b\n\n(Verse 2)\nv1\nv2\nv3\nv4\nv5\n\n"
          "chorus a\nchorus b\n")


def test_split_drops_labels_handles_crlf_and_balances():
    chunks = split_chunks(LYRICS)
    assert [c.text.splitlines() for c in chunks] == [
        ["line one", "line two"], ["chorus a", "chorus b"], ["v1", "v2", "v3"], ["v4", "v5"], ["chorus a", "chorus b"]]
    assert [c.index for c in chunks] == [0, 1, 2, 3, 4]
    assert chunks[4].repeat_of == 1 and chunks[1].repeat_of is None


def test_long_stanza_is_cut_into_balanced_pieces():
    stanza = "\n".join(f"l{i}" for i in range(9))
    assert [len(c.text.splitlines()) for c in split_chunks(stanza)] == [3, 3, 3]
    stanza = "\n".join(f"l{i}" for i in range(4))
    assert [len(c.text.splitlines()) for c in split_chunks(stanza)] == [4]


def test_repeat_ignores_case_and_punctuation():
    chunks = split_chunks("Oh, yeah!\nGo now\n\noh yeah\ngo now.")
    assert chunks[1].repeat_of == 0


def test_empty_lyrics_give_no_chunks():
    assert split_chunks("\n\n[Chorus]\n") == []
    assert split_chunks("") == []


def test_word_diff_marks_missing_and_wrong():
    r = word_diff("his palms are sweaty", "his palm are")
    assert [t["status"] for t in r["tokens"]] == ["ok", "wrong", "ok", "missing"] and r["score"] == 50
    assert [t["word"] for t in r["tokens"]] == ["his", "palms", "are", "sweaty"]


def test_word_diff_marks_extra_words_and_ignores_case():
    r = word_diff("I am here", "i am really here")
    assert [(t["word"], t["status"]) for t in r["tokens"]] == [
        ("i", "ok"), ("am", "ok"), ("really", "extra"), ("here", "ok")]
    assert r["score"] == 100


def test_word_diff_with_empty_answer_scores_zero():
    assert word_diff("one two", "")["score"] == 0
    assert word_diff("", "")["score"] == 0
