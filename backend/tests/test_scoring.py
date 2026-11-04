from app.scoring import final_score


def test_weighted_final_score():
    assert final_score(80, 90) == 86


def test_without_listening_uses_conversation_only():
    assert final_score(None, 73) == 73
