from types import SimpleNamespace

import pytest

from app.exercises import is_correct, normalize


def ex(answers):
    return SimpleNamespace(answers=answers)


@pytest.mark.parametrize("given", ["I'm going home.", "i am going home", "I’m going home", "  I'm   going home!  "])
def test_equivalent_forms_are_correct(given):
    assert is_correct(ex(answers=["I'm going home"]), given)


def test_dont_and_do_not_match():
    assert is_correct(ex(answers=["She doesn't like it"]), "she does not like it")


def test_wrong_word_is_wrong():
    assert not is_correct(ex(answers=["I went"]), "I goed")


def test_curly_quotes_in_accepted_answer_also_normalize():
    assert is_correct(ex(answers=["It’s “fine”"]), "it's fine")


def test_wont_and_cant_expand():
    assert normalize("I won't go, I can't") == "i will not go i can not"
    assert normalize("I cannot") == "i can not"


def test_s_and_d_stay_as_typed():
    assert normalize("He's here") == "he's here"
    assert not is_correct(ex(answers=["He is here"]), "He's here")
