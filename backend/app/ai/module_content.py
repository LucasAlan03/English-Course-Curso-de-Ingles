from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from app.ai.prompts import render
from app.ai.structured import generate_structured
from app.content import Module, Scenario
from app.providers.base import Msg, TextModel
from app.usage import UsageTracker


class ModuleDraft(BaseModel):
    theory_md: str
    scenario: Scenario
    target_structures: list[str] = Field(min_length=1)


def generate_module(entry: dict, model: TextModel, tracker: UsageTracker, prompts_dir: str) -> Module:
    """Draft one module's content with the AI; id, level, title, order and source come from the outline."""
    system = render("module_content", prompts_dir, level=entry["level"], title=entry["title"], source=entry["source"])
    draft = generate_structured(model, system, [Msg("user", "Write the module now.")], ModuleDraft, tracker)
    return Module(
        id=entry["id"], level=entry["level"], title=entry["title"], order=entry["order"], source=entry["source"],
        theory_md=draft.theory_md, scenario=draft.scenario, target_structures=draft.target_structures,
    )


def generate_all(
    entries: list[dict], out_dir: str, model: TextModel, tracker: UsageTracker, prompts_dir: str,
    only: str | None = None, force: bool = False,
) -> list[str]:
    """Write one YAML file per outline entry; existing files are kept unless `force` is set."""
    directory = Path(out_dir)
    directory.mkdir(parents=True, exist_ok=True)
    written = []
    for entry in entries:
        if only and entry["id"] != only:
            continue
        path = directory / f"{entry['id']}.yaml"
        if path.exists() and not force:
            continue
        module = generate_module(entry, model, tracker, prompts_dir)
        path.write_text(yaml.safe_dump(module.model_dump(), allow_unicode=True, sort_keys=False), encoding="utf-8")
        written.append(entry["id"])
    return written
