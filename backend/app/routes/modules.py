from datetime import date

from fastapi import APIRouter, Depends

from app.deps import AppDeps, get_deps
from app.errors import AppError
from app.goals import pillars_for_day, streak

router = APIRouter()


def completed_module_ids(deps: AppDeps) -> set[str]:
    """A module is completed once one of its lessons has been finished."""
    rows = deps.conn.execute(
        "SELECT DISTINCT module_id FROM sessions WHERE kind = 'lesson' AND is_finished = 1 AND module_id IS NOT NULL"
    ).fetchall()
    return {r["module_id"] for r in rows}


@router.get("/modules")
def list_modules(deps: AppDeps = Depends(get_deps)):
    done = completed_module_ids(deps)
    levels: dict[str, dict] = {}
    for m in deps.content.all():
        level = levels.setdefault(m.level, {"level": m.level, "total": 0, "completed": 0, "modules": []})
        completed = m.id in done
        level["total"] += 1
        level["completed"] += int(completed)
        level["modules"].append({"id": m.id, "title": m.title, "order": m.order, "completed": completed})
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

    next_module = next(
        ({"id": m.id, "title": m.title, "level": m.level} for m in deps.content.all() if m.id not in done),
        None,
    )
    return {
        "reviews_due": reviews_due,
        "next_module": next_module,
        "pillars": pillars_for_day(deps.conn, today),
        "streak": streak(deps.conn, today),
        "usage": deps.tracker.status(),
    }
