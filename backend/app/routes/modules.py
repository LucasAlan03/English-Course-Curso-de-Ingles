from datetime import date

from fastapi import APIRouter, Depends

from app.content import EXERCISE_COUNT
from app.deps import AppDeps, get_deps
from app.errors import AppError
from app.exams import LEVELS, exam_status, level_unlocked, passed_levels
from app.daily_plan import day_plan, streak

router = APIRouter()


def completed_module_ids(deps: AppDeps) -> set[str]:
    """A module is completed once all its lesson exercises have been answered."""
    rows = deps.conn.execute(
        "SELECT module_id FROM exercise_attempts WHERE kind = 'lesson' GROUP BY module_id HAVING COUNT(*) >= ?",
        (EXERCISE_COUNT,),
    ).fetchall()
    return {r["module_id"] for r in rows}


@router.get("/modules")
def list_modules(deps: AppDeps = Depends(get_deps)):
    done = completed_module_ids(deps)
    passed = passed_levels(deps)
    levels: dict[str, dict] = {}
    for m in deps.content.all():
        level = levels.setdefault(m.level, {
            "level": m.level, "total": 0, "completed": 0, "modules": [],
            "unlocked": level_unlocked(deps, m.level, passed),
        })
        completed = m.id in done
        level["total"] += 1
        level["completed"] += int(completed)
        level["modules"].append({"id": m.id, "title": m.title, "order": m.order, "completed": completed})
    for level in levels.values():
        level["exam"] = exam_status(deps, level["level"], done, passed)
    return {"levels": list(levels.values())}


@router.get("/modules/{module_id}")
def get_module(module_id: str, deps: AppDeps = Depends(get_deps)):
    try:
        module = deps.content.get(module_id)
    except KeyError:
        raise AppError("module_not_found", 404, "Módulo não encontrado.")
    return {**module.model_dump(), "completed": module_id in completed_module_ids(deps)}


@router.get("/home")
def home(deps: AppDeps = Depends(get_deps)):
    today = deps.clock.today()
    done = completed_module_ids(deps)
    known = set(deps.content.ids())

    rows = deps.conn.execute(
        "SELECT module_id, next_due FROM reviews WHERE next_due <= ? ORDER BY next_due, module_id",
        (today.isoformat(),),
    ).fetchall()
    reviews_due = [
        {
            "module_id": r["module_id"],
            "title": deps.content.get(r["module_id"]).title,
            "next_due": r["next_due"],
            "overdue_days": (today - date.fromisoformat(r["next_due"])).days,
        }
        for r in rows if r["module_id"] in known
    ]

    passed = passed_levels(deps)
    open_levels = {lv for lv in LEVELS if level_unlocked(deps, lv, passed)}
    next_module = next(
        ({"id": m.id, "title": m.title, "level": m.level} for m in deps.content.all()
         if m.id not in done and m.level in open_levels),
        None,
    )
    exam_ready = next((lv for lv in LEVELS if lv in open_levels and lv not in passed
                       and exam_status(deps, lv, done, passed)["available"]), None)
    return {
        "exam_ready": exam_ready,
        "reviews_due": reviews_due,
        "next_module": next_module,
        "today": day_plan(deps, today),
        "streak": streak(deps, today),
        "usage": deps.tracker.status(),
    }
