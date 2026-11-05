"""Level exams (B1, B2, C1): unlock rules, drawing, grading and score. No AI."""

import json
import random
from datetime import timezone

from app.deps import AppDeps
from app.errors import AppError

EXAM_SIZE = 30
PASS_PERCENT = 75
LEVELS = ("B1", "B2", "C1")


def _completed(deps: AppDeps) -> set[str]:
    from app.routes.modules import completed_module_ids

    return completed_module_ids(deps)


def passed_levels(deps: AppDeps) -> set[str]:
    rows = deps.conn.execute("SELECT DISTINCT level FROM exam_runs WHERE passed = 1").fetchall()
    return {r["level"] for r in rows}


def level_unlocked(deps: AppDeps, level: str, passed: set[str] | None = None) -> bool:
    index = LEVELS.index(level)
    if index == 0:
        return True
    return LEVELS[index - 1] in (passed if passed is not None else passed_levels(deps))


def ensure_module_unlocked(deps: AppDeps, module_id: str) -> None:
    level = deps.content.get(module_id).level
    if not level_unlocked(deps, level):
        previous = LEVELS[LEVELS.index(level) - 1]
        raise AppError("level_locked", 403, f"Nível trancado: passe na prova de {previous}.")


def exam_status(deps: AppDeps, level: str, done: set[str] | None = None, passed: set[str] | None = None) -> dict:
    done = done if done is not None else _completed(deps)
    passed = passed if passed is not None else passed_levels(deps)
    missing = sum(1 for m in deps.content.all() if m.level == level and m.id not in done)
    best = deps.conn.execute("SELECT MAX(score) FROM exam_runs WHERE level = ? AND finished_at IS NOT NULL",
                             (level,)).fetchone()[0]
    open_run = deps.conn.execute("SELECT id FROM exam_runs WHERE level = ? AND finished_at IS NULL "
                                 "ORDER BY id DESC LIMIT 1", (level,)).fetchone()
    return {
        "available": missing == 0 and level_unlocked(deps, level, passed) and bool(deps.content.exam(level)),
        "missing_modules": missing,
        "passed": level in passed,
        "best_score": best,
        "open_run_id": open_run["id"] if open_run else None,
    }


def start_exam(deps: AppDeps, level: str) -> int:
    if level not in LEVELS:
        raise AppError("level_not_found", 404, "Nível não encontrado.")
    status = exam_status(deps, level)
    if status["open_run_id"] is not None:
        return status["open_run_id"]
    if not status["available"]:
        raise AppError("exam_locked", 409, "Conclua todos os módulos do nível para liberar a prova.")
    bank = deps.content.exam(level)
    ids = [q.id for q in random.Random().sample(bank, min(EXAM_SIZE, len(bank)))]
    cur = deps.conn.execute(
        "INSERT INTO exam_runs (level, question_ids, started_at) VALUES (?, ?, ?)",
        (level, json.dumps(ids), deps.clock.now().astimezone(timezone.utc).isoformat()),
    )
    deps.conn.commit()
    return cur.lastrowid
