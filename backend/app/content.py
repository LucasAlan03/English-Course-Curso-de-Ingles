from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel

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


class ContentRepo:
    def __init__(self, modules: list[Module]):
        self._modules = sorted(modules, key=lambda m: (LEVEL_RANK[m.level], m.order))
        self._by_id = {m.id: m for m in self._modules}

    @classmethod
    def load(cls, directory: str) -> "ContentRepo":
        modules: list[Module] = []
        seen: set[str] = set()
        for path in sorted(Path(directory).glob("*.yaml")):
            module = Module(**yaml.safe_load(path.read_text(encoding="utf-8")))
            if module.id in seen:
                raise ValueError(f"duplicate module id: {module.id}")
            seen.add(module.id)
            modules.append(module)
        return cls(modules)

    def all(self) -> list[Module]:
        return list(self._modules)

    def get(self, module_id: str) -> Module:
        return self._by_id[module_id]

    def ids(self) -> list[str]:
        return [m.id for m in self._modules]
