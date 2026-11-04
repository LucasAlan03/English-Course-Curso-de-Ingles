from datetime import timedelta, timezone

from app.ai.schemas import MistakeOut
from app.db import insert
from app.deps import AppDeps

PULL_FORWARD_AFTER = 3  # mistakes on one module...
PULL_FORWARD_WINDOW_DAYS = 7  # ...within this many days bring its review to tomorrow


def record_mistakes(deps: AppDeps, session_id: int, mistakes: list[MistakeOut], session_module_id: str | None) -> None:
    """Save a report's mistakes and pull forward the reviews of modules that keep failing.

    A module session files every mistake under its own module; otherwise the AI's suggestion
    is used only if it is a real module id.
    """
    now = deps.clock.now().astimezone(timezone.utc).isoformat()
    known = set(deps.content.ids())
    touched: set[str] = set()
    for m in mistakes:
        module_id = session_module_id or (m.module_id if m.module_id in known else None)
        insert(deps.conn, "mistakes", session_id=session_id, module_id=module_id, said=m.said,
               corrected=m.corrected, explanation=m.explanation, created_at=now)
        if module_id:
            touched.add(module_id)
    pull_forward_reviews(deps, touched)


def pull_forward_reviews(deps: AppDeps, module_ids: set[str]) -> None:
    since = (deps.clock.now().astimezone(timezone.utc) - timedelta(days=PULL_FORWARD_WINDOW_DAYS)).isoformat()
    tomorrow = (deps.clock.today() + timedelta(days=1)).isoformat()
    for module_id in module_ids:
        recent = deps.conn.execute(
            "SELECT COUNT(*) FROM mistakes WHERE module_id = ? AND created_at >= ?", (module_id, since)
        ).fetchone()[0]
        review = deps.conn.execute("SELECT next_due FROM reviews WHERE module_id = ?", (module_id,)).fetchone()
        if recent >= PULL_FORWARD_AFTER and review and review["next_due"] > tomorrow:
            deps.conn.execute("UPDATE reviews SET next_due = ? WHERE module_id = ?", (tomorrow, module_id))
            deps.conn.commit()
