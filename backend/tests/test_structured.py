import json
import re
from pathlib import Path

import pytest
from pydantic import BaseModel, ValidationError

from app.ai.prompts import PROMPT_VARS, render
from app.ai.schemas import ListeningItem, ListeningSet, Report
from app.ai.structured import generate_structured
from app.errors import InvalidAIOutput
from app.providers.base import Msg
from app.providers.fakes import FakeTextModel

PROMPTS = Path(__file__).parent.parent / "prompts"


class Thing(BaseModel):
    name: str
    n: int


def ask(model, tracker):
    return generate_structured(model, "sys", [Msg("user", "go")], Thing, tracker)


def test_valid_json_parsed(tracker):
    model = FakeTextModel([json.dumps({"name": "a", "n": 1})])
    assert ask(model, tracker) == Thing(name="a", n=1)


def test_fenced_json_accepted(tracker):
    model = FakeTextModel(['```json\n{"name": "a", "n": 2}\n```'])
    assert ask(model, tracker).n == 2


def test_retries_once_then_succeeds(tracker, conn):
    model = FakeTextModel(["not json", '{"name": "a", "n": 3}'])
    assert ask(model, tracker).n == 3
    assert len(model.calls) == 2
    assert "valid JSON" in model.calls[1][1][-1].content
    assert conn.execute("SELECT COUNT(*) FROM api_usage").fetchone()[0] == 2


def test_invalid_twice_raises_invalid_ai_output(tracker):
    model = FakeTextModel(["nope", '{"name": 1}'])
    with pytest.raises(InvalidAIOutput):
        ask(model, tracker)
    assert len(model.calls) == 2


def choice(i):
    return {"kind": "choice", "audio_text": f"a{i}", "prompt": f"q{i}", "options": ["x", "y", "z"],
            "answer": "x", "explanation": "e"}


def gap(i):
    return {"kind": "gap", "audio_text": f"a{i}", "prompt": f"q{i} ___", "answer": "went", "explanation": "e"}


def test_listening_set_requires_3_choice_2_gap():
    ListeningSet(items=[choice(1), choice(2), choice(3), gap(4), gap(5)])
    with pytest.raises(ValidationError):
        ListeningSet(items=[choice(1), choice(2), gap(3), gap(4), gap(5)])
    with pytest.raises(ValidationError):
        ListeningSet(items=[choice(1), choice(2), choice(3), choice(4), gap(5)])


def test_listening_set_accepts_review_size():
    ListeningSet(items=[choice(1), choice(2), gap(3)])


def test_choice_answer_must_be_among_options():
    bad = choice(1) | {"answer": "w"}
    with pytest.raises(ValidationError):
        ListeningItem(**bad)


def test_report_score_range():
    base = {"mistakes": [], "natural_expressions": [], "strengths": []}
    Report(**base, score=100)
    with pytest.raises(ValidationError):
        Report(**base, score=101)


def test_render_substitutes_and_missing_var_raises(tmp_path):
    (tmp_path / "t.md").write_text("Hello {{name}}, level {{level}}.", encoding="utf-8")
    assert render("t", str(tmp_path), name="Ana", level="B1") == "Hello Ana, level B1."
    with pytest.raises(KeyError):
        render("t", str(tmp_path), name="Ana")


@pytest.mark.parametrize("name", sorted(PROMPT_VARS))
def test_shipped_prompts_use_exactly_the_documented_variables(name):
    text = (PROMPTS / f"{name}.md").read_text(encoding="utf-8")
    assert set(re.findall(r"\{\{(\w+)\}\}", text)) == PROMPT_VARS[name]
