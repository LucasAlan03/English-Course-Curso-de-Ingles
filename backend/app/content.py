import re
from collections import Counter
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field

from app.exercises import normalize

LEVEL_RANK = {"B1": 0, "B2": 1, "C1": 2}


class Scenario(BaseModel):
    title: str
    character: str
    goal: str


class Module(BaseModel):
    id: str
    level: Literal["B1", "B2", "C1"]
    title: str
    order: int
    theory_md: str
    scenario: Scenario
    target_structures: list[str]
    source: str


ExerciseType = Literal["choice", "listen", "gap", "dictation", "fix", "transform", "order", "translate"]

BLOCK_PLAN: dict[int, dict[str, int]] = {
    1: {"choice": 5, "listen": 2, "gap": 2},
    2: {"choice": 3, "gap": 1, "fix": 2, "order": 2, "dictation": 1},
    3: {"choice": 2, "listen": 1, "fix": 1, "transform": 2, "translate": 2, "dictation": 1},
}
EXERCISE_COUNT = sum(sum(plan.values()) for plan in BLOCK_PLAN.values())


class Exercise(BaseModel):
    id: str
    block: Literal[1, 2, 3]
    type: ExerciseType
    prompt: str
    answers: list[str] = Field(min_length=1)
    explanation: str
    options: list[str] | None = None
    words: list[str] | None = None
    audio_text: str | None = None
    prompt_pt: str | None = None
    glossary: dict[str, str] = {}


def _choice_problems(item, label: str) -> list[str]:
    options = item.options or []
    if not 3 <= len(options) <= 4:
        return [f"{item.id}: {label} needs 3-4 options"]
    accepted = {normalize(a) for a in item.answers}
    hits = sum(1 for o in options if normalize(o) in accepted)
    if hits != 1:
        return [f"{item.id}: {label} needs exactly one correct option (found {hits})"]
    return []


def item_problems(item) -> list[str]:
    """Rules that apply to a single exercise or exam question."""
    problems: list[str] = []
    audio_text = getattr(item, "audio_text", None)
    if item.type == "choice":
        problems += _choice_problems(item, "choice")
    if item.type in ("listen", "dictation") and not audio_text:
        problems.append(f"{item.id}: {item.type} needs audio_text")
    if item.type == "listen" and item.options:
        problems += _choice_problems(item, "listen")
    if item.type == "dictation" and audio_text and normalize(audio_text) not in {normalize(a) for a in item.answers}:
        problems.append(f"{item.id}: dictation answers must contain audio_text")
    if item.type == "order":
        if not item.words:
            problems.append(f"{item.id}: order needs words")
        elif sorted(normalize(item.answers[0]).split()) != sorted(normalize(" ".join(item.words)).split()):
            problems.append(f"{item.id}: order words do not match the answer")
    if item.type == "translate" and item.prompt_pt:
        problems.append(f"{item.id}: translate must not have prompt_pt")
    if item.type != "translate" and not item.prompt_pt:
        problems.append(f"{item.id}: prompt_pt is required")
    if len(item.glossary) > 4:
        problems.append(f"{item.id}: glossary has more than 4 entries")
    forbidden = {normalize(a) for a in item.answers} | {normalize(o) for o in item.options or []}
    for word in item.glossary:
        if not re.search(rf"(?<![A-Za-z']){re.escape(word)}(?![A-Za-z'])", item.prompt, re.IGNORECASE):
            problems.append(f"{item.id}: glossary word '{word}' is not in the prompt")
        if normalize(word) in forbidden:
            problems.append(f"{item.id}: glossary word '{word}' gives away the answer")
    return problems


def validate_exercises(exercises: list[Exercise]) -> list[str]:
    problems: list[str] = []
    if len(exercises) != EXERCISE_COUNT:
        problems.append(f"expected {EXERCISE_COUNT} exercises, found {len(exercises)}")
    expected_ids = [f"e{i:02d}" for i in range(1, EXERCISE_COUNT + 1)]
    if sorted(e.id for e in exercises) != expected_ids:
        problems.append(f"ids must be exactly e01..e{EXERCISE_COUNT}")
    for block, plan in BLOCK_PLAN.items():
        found = Counter(e.type for e in exercises if e.block == block)
        if dict(found) != plan:
            problems.append(f"block {block}: expected {plan}, found {dict(found)}")
    seen: set[tuple[str, str | None]] = set()
    for e in exercises:
        problems += item_problems(e)
        key = (normalize(e.prompt), e.audio_text)
        if key in seen:
            problems.append(f"{e.id}: duplicate prompt")
        seen.add(key)
    return problems


class ContentRepo:
    def __init__(self, modules: list[Module], exercises: dict[str, list[Exercise]] | None = None):
        self._modules = sorted(modules, key=lambda m: (LEVEL_RANK[m.level], m.order))
        self._by_id = {m.id: m for m in self._modules}
        self._exercises = exercises or {}

    @classmethod
    def load(cls, directory: str, exercises_dir: str | None = None) -> "ContentRepo":
        modules: list[Module] = []
        seen: set[str] = set()
        for path in sorted(Path(directory).glob("*.yaml")):
            module = Module(**yaml.safe_load(path.read_text(encoding="utf-8")))
            if module.id in seen:
                raise ValueError(f"duplicate module id: {module.id}")
            seen.add(module.id)
            modules.append(module)
        exercises: dict[str, list[Exercise]] = {}
        if exercises_dir and Path(exercises_dir).is_dir():
            for path in sorted(Path(exercises_dir).glob("*.yaml")):
                data = yaml.safe_load(path.read_text(encoding="utf-8"))
                items = [Exercise(**e) for e in data["exercises"]]
                exercises[data["module_id"]] = sorted(items, key=lambda e: e.id)
        return cls(modules, exercises)

    def exercises(self, module_id: str) -> list[Exercise]:
        return list(self._exercises.get(module_id, []))

    def all(self) -> list[Module]:
        return list(self._modules)

    def get(self, module_id: str) -> Module:
        return self._by_id[module_id]

    def ids(self) -> list[str]:
        return [m.id for m in self._modules]
