from collections import Counter
from pathlib import Path

import pytest
import yaml

from app.content import ContentRepo

CURRICULUM = Path(__file__).parent.parent / "content" / "curriculum.yaml"


def write_module(directory, module_id, level="B1", order=1, title="T"):
    data = {
        "id": module_id, "level": level, "title": title, "order": order,
        "theory_md": "Some theory.", "source": "test",
        "scenario": {"title": "S", "character": "A barista", "goal": "Order a coffee"},
        "target_structures": ["past simple"],
    }
    (directory / f"{module_id}.yaml").write_text(yaml.safe_dump(data), encoding="utf-8")


def test_load_orders_by_level_then_order(tmp_path):
    write_module(tmp_path, "c1_a", "C1", 1)
    write_module(tmp_path, "b1_b", "B1", 2)
    write_module(tmp_path, "b1_a", "B1", 1)
    repo = ContentRepo.load(str(tmp_path))
    assert repo.ids() == ["b1_a", "b1_b", "c1_a"]
    assert [m.id for m in repo.all()] == ["b1_a", "b1_b", "c1_a"]


def test_get_unknown_raises_keyerror(tmp_path):
    write_module(tmp_path, "b1_a")
    repo = ContentRepo.load(str(tmp_path))
    assert repo.get("b1_a").scenario.character == "A barista"
    with pytest.raises(KeyError):
        repo.get("nope")


def test_duplicate_ids_rejected(tmp_path):
    write_module(tmp_path, "b1_a")
    (tmp_path / "copy.yaml").write_text((tmp_path / "b1_a.yaml").read_text(encoding="utf-8"), encoding="utf-8")
    with pytest.raises(ValueError):
        ContentRepo.load(str(tmp_path))


def test_curriculum_outline_has_26_modules_10_9_7():
    modules = yaml.safe_load(CURRICULUM.read_text(encoding="utf-8"))["modules"]
    assert len(modules) == 26
    assert len({m["id"] for m in modules}) == 26
    assert Counter(m["level"] for m in modules) == {"B1": 10, "B2": 9, "C1": 7}
    assert all(m["title"] and m["source"] for m in modules)
