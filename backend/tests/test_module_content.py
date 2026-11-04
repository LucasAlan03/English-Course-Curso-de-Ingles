import json

import pytest
import yaml

from app.ai.module_content import generate_all, generate_module
from app.content import ContentRepo, Module
from app.errors import InvalidAIOutput
from app.providers.fakes import FakeTextModel

ENTRY = {"id": "b1_futures", "level": "B1", "title": "Futuros (will / going to)", "order": 2,
         "source": "CEFR B1 - test source"}
OTHER = {"id": "b2_passive_voice", "level": "B2", "title": "Voz passiva", "order": 1, "source": "CEFR B2 - test"}


def draft(extra=None):
    data = {"theory_md": "# Futuros\n- **will** para decisões", "target_structures": ["will", "going to"],
            "scenario": {"title": "Planning a trip", "character": "A travel agent", "goal": "Plan a holiday"}}
    return json.dumps({**data, **(extra or {})})


def test_generate_module_merges_the_outline_with_the_ai_draft(tracker, settings):
    model = FakeTextModel([draft()])
    module = generate_module(ENTRY, model, tracker, settings.prompts_dir)
    assert isinstance(module, Module)
    assert (module.id, module.level, module.order, module.source) == ("b1_futures", "B1", 2, "CEFR B1 - test source")
    assert module.scenario.character == "A travel agent" and module.target_structures == ["will", "going to"]
    system = model.calls[0][0]
    assert "B1" in system and "Futuros (will / going to)" in system and "CEFR B1 - test source" in system


def test_generate_module_rejects_an_incomplete_draft(tracker, settings):
    model = FakeTextModel(['{"theory_md": "x"}', '{"theory_md": "x"}'])
    with pytest.raises(InvalidAIOutput):
        generate_module(ENTRY, model, tracker, settings.prompts_dir)


def test_generate_all_writes_files_and_skips_existing(tmp_path, tracker, settings):
    out = tmp_path / "out"
    written = generate_all([ENTRY, OTHER], str(out), FakeTextModel([draft(), draft()]), tracker, settings.prompts_dir)
    assert written == ["b1_futures", "b2_passive_voice"]
    assert yaml.safe_load((out / "b1_futures.yaml").read_text(encoding="utf-8"))["title"] == ENTRY["title"]
    assert len(ContentRepo.load(str(out)).all()) == 2

    model = FakeTextModel([draft()])
    assert generate_all([ENTRY, OTHER], str(out), model, tracker, settings.prompts_dir) == []
    assert model.calls == []  # nothing regenerated


def test_generate_all_only_and_force(tmp_path, tracker, settings):
    out = tmp_path / "out"
    generate_all([ENTRY, OTHER], str(out), FakeTextModel([draft()]), tracker, settings.prompts_dir, only="b2_passive_voice")
    assert sorted(p.stem for p in out.glob("*.yaml")) == ["b2_passive_voice"]
    redo = generate_all([ENTRY, OTHER], str(out), FakeTextModel([draft({"theory_md": "new"})]), tracker,
                        settings.prompts_dir, only="b2_passive_voice", force=True)
    assert redo == ["b2_passive_voice"]
    assert yaml.safe_load((out / "b2_passive_voice.yaml").read_text(encoding="utf-8"))["theory_md"] == "new"
