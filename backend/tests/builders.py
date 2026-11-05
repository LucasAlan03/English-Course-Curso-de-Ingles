"""Small helpers shared by the API tests."""
import json
from datetime import datetime, timezone

import yaml

from app.db import insert


def write_module(directory, module_id, level="B1", order=1, title="A topic"):
    data = {
        "id": module_id, "level": level, "title": title, "order": order,
        "theory_md": "Some theory with *examples*.", "source": "test",
        "scenario": {"title": "At a cafe", "character": "A friendly barista", "goal": "Order a coffee"},
        "target_structures": ["past simple", "past continuous"],
    }
    (directory / f"{module_id}.yaml").write_text(yaml.safe_dump(data), encoding="utf-8")


def listening_json(count=5):
    choices, gaps = (3, 2) if count == 5 else (2, 1)
    items = []
    for i in range(choices):
        items.append({"kind": "choice", "audio_text": f"I went home {i}", "prompt": f"What happened {i}?",
                      "options": ["went", "go", "gone"], "answer": "went", "explanation": "Past simple."})
    for i in range(gaps):
        items.append({"kind": "gap", "audio_text": f"She went out {i}", "prompt": f"She ___ out {i}.",
                      "answer": "went", "explanation": "Past simple de go."})
    return json.dumps({"items": items})


def report_json(score=80, mistakes=None):
    return json.dumps({
        "mistakes": mistakes if mistakes is not None else [],
        "natural_expressions": ["How was your weekend?"], "strengths": ["Good vocabulary"], "score": score,
    })


def make_session(deps, kind="lesson", module_id="b1_past_simple_continuous", **cols):
    now = deps.clock.now().astimezone(timezone.utc).isoformat()
    return insert(deps.conn, "sessions", kind=kind, module_id=module_id, started_at=now, **cols)


def add_user_message(deps, session_id, text="I went to the park yesterday."):
    insert(deps.conn, "messages", session_id=session_id, role="user", text=text,
           created_at=datetime.now(timezone.utc).isoformat())


def writing_json(score=75, mistakes=None):
    return json.dumps({
        "corrected_text": "Last weekend I went to the beach.",
        "improved_text": "Last weekend I spent a lovely day at the beach.",
        "mistakes": mistakes if mistakes is not None else [
            {"said": "I goed to the beach", "corrected": "I went to the beach",
             "explanation": "Passado irregular.", "module_id": "b1_past_simple_continuous"}],
        "score": score,
    })


_ITEM_TEMPLATES = {
    "choice": lambda n: {"prompt": f"Yesterday I ___ to the park ({n}).", "prompt_pt": f"Ontem eu fui ao parque ({n}).",
                         "options": ["went", "go", "gone"], "answers": ["went"], "glossary": {"park": "parque"}},
    "listen": lambda n: {"prompt": f"Where did she go? ({n})", "prompt_pt": f"Aonde ela foi? ({n})",
                         "audio_text": f"She went to the market {n}.", "options": ["market", "school", "bank"],
                         "answers": ["market"]},
    "gap": lambda n: {"prompt": f"She ___ (watch) a series last night ({n}).",
                      "prompt_pt": f"Ela assistiu a uma série ontem à noite ({n}).", "answers": ["watched"]},
    "fix": lambda n: {"prompt": f"I goed home early ({n}).", "prompt_pt": f"Eu fui para casa cedo ({n}).",
                      "answers": [f"I went home early ({n})", f"I went home early {n}"]},
    "order": lambda n: {"prompt": f"Put the words in order ({n}).", "prompt_pt": f"Coloque as palavras em ordem ({n}).",
                        "words": ["cooking", "she", "was"], "answers": ["she was cooking"]},
    "dictation": lambda n: {"prompt": f"Write what you hear ({n}).", "prompt_pt": f"Escreva o que ouvir ({n}).",
                            "audio_text": f"We were watching a movie at {n} o'clock",
                            "answers": [f"We were watching a movie at {n} o'clock"]},
    "transform": lambda n: {"prompt": f"Rewrite in the past: I eat pizza ({n}).",
                            "prompt_pt": f"Reescreva no passado: eu como pizza ({n}).",
                            "answers": ["I ate pizza"]},
    "translate": lambda n: {"prompt": f"Eu estava dormindo quando você ligou ({n}).",
                            "answers": ["I was sleeping when you called"]},
}


def valid_exercises() -> list[dict]:
    """27 exercise dicts that satisfy every validator rule."""
    from app.content import BLOCK_PLAN

    items, n = [], 0
    for block, plan in BLOCK_PLAN.items():
        for kind, count in plan.items():
            for _ in range(count):
                n += 1
                item = {"id": f"e{n:02d}", "block": block, "type": kind,
                        "explanation": "Past simple para ação terminada."}
                item.update(_ITEM_TEMPLATES[kind](n))
                items.append(item)
    return items


def correct_answers() -> dict[str, str]:
    return {e["id"]: e["answers"][0] for e in valid_exercises()}


def write_exercises(directory, module_id, exercises=None):
    data = {"module_id": module_id, "exercises": exercises if exercises is not None else valid_exercises()}
    (directory / f"{module_id}.yaml").write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")


def complete_module(deps, module_id, day="2026-11-03", correct=1):
    """Insert the 27 lesson attempts that mark a module as completed."""
    for i in range(1, 28):
        insert(deps.conn, "exercise_attempts", module_id=module_id, exercise_id=f"e{i:02d}", kind="lesson",
               answer="x", correct=correct, seconds=10, day=day, created_at=f"{day}T12:00:00+00:00")


EXAM_TYPES_CYCLE = ["choice", "gap", "fix", "transform", "order", "translate"]


def valid_exam(module_ids, size=40) -> list[dict]:
    """A level exam bank that satisfies every validator rule, cycling through the modules."""
    questions = []
    for n in range(1, size + 1):
        kind = EXAM_TYPES_CYCLE[(n - 1) % len(EXAM_TYPES_CYCLE)]
        item = {"id": f"q{n:02d}", "type": kind, "module_id": module_ids[(n - 1) % len(module_ids)],
                "explanation": "Explicação curta."}
        item.update(_ITEM_TEMPLATES[kind](100 + n))
        questions.append(item)
    return questions


def exam_answers(module_ids) -> dict[str, str]:
    return {q["id"]: q["answers"][0] for q in valid_exam(module_ids)}


def write_exam(directory, level, questions):
    data = {"level": level, "questions": questions}
    (directory / f"{level.lower()}.yaml").write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
