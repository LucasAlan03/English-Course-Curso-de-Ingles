"""The shipped course content: 46 modules, 27 exercises each, 3 level exam banks."""
from collections import Counter
from pathlib import Path

import pytest
import yaml

from app.config import Settings
from app.content import ContentRepo, validate_exam, validate_exercises

SETTINGS = Settings(_env_file=None)
REPO = ContentRepo.load(SETTINGS.content_dir, SETTINGS.exercises_dir, SETTINGS.exams_dir)
EX_DIR = Path(SETTINGS.exercises_dir)
CURRICULUM = Path(SETTINGS.content_dir).parent / "curriculum.yaml"

MODULE_IDS = [
    "b1_past_simple", "b1_past_continuous", "b1_present_perfect", "b1_future_will", "b1_future_going_to",
    "b1_future_present_continuous", "b1_first_conditional", "b1_second_conditional", "b1_modals_obligation",
    "b1_modals_advice", "b1_comparatives", "b1_superlatives", "b1_prepositions_time", "b1_prepositions_place",
    "b1_prepositions_movement", "b1_verb_ing", "b1_verb_to", "b1_phrasal_verbs", "b1_relative_clauses",
    "b2_present_perfect_continuous", "b2_past_perfect_narrative", "b2_third_conditional", "b2_mixed_conditionals",
    "b2_passive_basic", "b2_passive_advanced", "b2_reported_statements", "b2_reported_questions",
    "b2_deduction_present", "b2_deduction_past", "b2_used_to_would", "b2_be_used_to", "b2_wish_present",
    "b2_wish_past", "b2_contrast", "b2_argumentation",
    "c1_inversion_negative", "c1_inversion_conditional", "c1_it_cleft", "c1_wh_cleft", "c1_past_modals_criticism",
    "c1_past_modals_possibility", "c1_causative", "c1_hedging", "c1_participle_clauses", "c1_collocations",
    "c1_idioms",
]


def test_real_curriculum_has_the_46_modules_in_order():
    assert REPO.ids() == MODULE_IDS
    assert Counter(m.level for m in REPO.all()) == {"B1": 19, "B2": 16, "C1": 11}


def test_module_files_match_the_outline():
    outline = {m["id"]: m for m in yaml.safe_load(CURRICULUM.read_text(encoding="utf-8"))["modules"]}
    for m in REPO.all():
        assert (m.level, m.title, m.order) == (outline[m.id]["level"], outline[m.id]["title"], outline[m.id]["order"])


@pytest.mark.parametrize("module_id", MODULE_IDS)
def test_every_module_has_theory_with_a_common_mistake_and_a_scenario(module_id):
    m = REPO.get(module_id)
    assert len(m.theory_md) > 150 and "Erro comum" in m.theory_md
    assert m.scenario.title and m.scenario.character and m.scenario.goal
    assert 3 <= len(m.target_structures) <= 4


def test_all_46_modules_have_exercises():
    assert all((EX_DIR / f"{m}.yaml").exists() for m in MODULE_IDS)
    assert sorted(p.stem for p in EX_DIR.glob("*.yaml")) == sorted(MODULE_IDS)


@pytest.mark.parametrize("module_id", MODULE_IDS)
def test_real_exercises_are_valid(module_id):
    assert validate_exercises(REPO.exercises(module_id)) == []


@pytest.mark.parametrize("level", ["B1", "B2", "C1"])
def test_real_exam_banks_are_valid(level):
    module_ids = [m.id for m in REPO.all() if m.level == level]
    assert validate_exam(level, REPO.exam(level), module_ids) == []
