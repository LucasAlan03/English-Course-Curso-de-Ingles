from app.content import ContentRepo, Exercise, validate_exercises
from builders import valid_exercises, write_exercises


def models(data):
    return [Exercise(**e) for e in data]


def test_valid_exercises_pass():
    assert validate_exercises(models(valid_exercises())) == []


def test_wrong_block_distribution_is_reported():
    data = valid_exercises()
    data[0]["type"] = "gap"  # e01 was a block-1 choice
    data[0].pop("options")
    problems = validate_exercises(models(data))
    assert any("block 1" in p for p in problems)


def test_wrong_count_is_reported():
    assert any("27" in p for p in validate_exercises(models(valid_exercises()[:-1])))


def test_choice_needs_exactly_one_correct_option():
    data = valid_exercises()
    data[0]["options"] = ["went", "goes", "go"]
    data[0]["answers"] = ["went", "goes"]
    assert any("e01" in p for p in validate_exercises(models(data)))


def test_order_words_must_match_answer():
    data = valid_exercises()
    order = next(e for e in data if e["type"] == "order")
    order["words"] = order["words"][:-1]
    assert any(order["id"] in p for p in validate_exercises(models(data)))


def test_listen_and_dictation_need_audio_text():
    data = valid_exercises()
    dictation = next(e for e in data if e["type"] == "dictation")
    dictation.pop("audio_text")
    assert any(dictation["id"] in p for p in validate_exercises(models(data)))


def test_duplicate_prompt_is_reported():
    data = valid_exercises()
    data[2]["prompt"] = data[1]["prompt"]
    assert any("e03" in p for p in validate_exercises(models(data)))


def test_glossary_cannot_give_away_the_answer():
    data = valid_exercises()
    data[0]["glossary"] = {"went": "foi"}
    assert any("e01" in p for p in validate_exercises(models(data)))


def test_glossary_word_must_be_in_prompt():
    data = valid_exercises()
    data[0]["glossary"] = {"beach": "praia"}
    assert any("e01" in p for p in validate_exercises(models(data)))


def test_prompt_pt_required_except_translate():
    data = valid_exercises()
    data[0].pop("prompt_pt")
    assert any("e01" in p for p in validate_exercises(models(data)))
    data = valid_exercises()
    tr = next(e for e in data if e["type"] == "translate")
    tr["prompt_pt"] = "algo"
    assert any(tr["id"] in p for p in validate_exercises(models(data)))


def test_repo_loads_exercises_and_tolerates_missing_files(tmp_path, module_dir):
    ex_dir = tmp_path / "ex"
    ex_dir.mkdir()
    write_exercises(ex_dir, "b1_futures")
    repo = ContentRepo.load(str(module_dir), str(ex_dir))
    assert len(repo.exercises("b1_futures")) == 27
    assert repo.exercises("b2_passive_voice") == []


def test_app_loads_exercises_from_settings(deps):
    assert len(deps.content.exercises("b1_past_simple_continuous")) == 27
