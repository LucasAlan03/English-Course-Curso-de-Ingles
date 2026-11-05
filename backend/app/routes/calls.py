import datetime as dt

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.call_time import app_seconds_for_day, call_minutes_for_day, external_minutes, session_seconds
from app.db import insert
from app.deps import AppDeps, get_deps
from app.errors import AppError
from app.sessions_repo import get_session

router = APIRouter()


class ExternalCall(BaseModel):
    date: dt.date
    source: str = Field(min_length=1, max_length=80)
    minutes: int = Field(ge=1, le=600)
    note: str | None = None


def _row(r) -> dict:
    return {k: r[k] for k in ("id", "date", "source", "minutes", "note")}


@router.post("/calls/external")
def add_external(body: ExternalCall, deps: AppDeps = Depends(get_deps)):
    item_id = insert(deps.conn, "call_logs", date=body.date.isoformat(), source=body.source.strip(),
                     minutes=body.minutes, note=body.note, created_at=deps.clock.now().isoformat())
    return _row(deps.conn.execute("SELECT * FROM call_logs WHERE id = ?", (item_id,)).fetchone())


@router.delete("/calls/external/{item_id}")
def delete_external(item_id: int, deps: AppDeps = Depends(get_deps)):
    if not deps.conn.execute("DELETE FROM call_logs WHERE id = ?", (item_id,)).rowcount:
        raise AppError("call_not_found", 404, "Registro não encontrado.")
    deps.conn.commit()
    return {"deleted": item_id}


@router.get("/calls")
def calls_for_day(date: dt.date, deps: AppDeps = Depends(get_deps)):
    rows = deps.conn.execute("SELECT * FROM call_logs WHERE date = ? ORDER BY id", (date.isoformat(),)).fetchall()
    return {
        "app_minutes": app_seconds_for_day(deps, date) // 60,
        "external": [_row(r) for r in rows],
        "total_minutes": call_minutes_for_day(deps, date),
    }


@router.get("/calls/summary")
def calls_summary(date: dt.date | None = None, deps: AppDeps = Depends(get_deps)):
    day = date or deps.clock.today()
    monday = day - dt.timedelta(days=day.weekday())
    week_app = sum(app_seconds_for_day(deps, monday + dt.timedelta(days=i)) for i in range(7))
    week = (week_app + external_minutes(deps, monday, monday + dt.timedelta(days=6)) * 60) // 60
    return {"day_minutes": call_minutes_for_day(deps, day), "week_minutes": week}


@router.get("/sessions/{session_id}/elapsed")
def session_elapsed(session_id: int, deps: AppDeps = Depends(get_deps)):
    session = get_session(deps.conn, session_id)
    now = None if session["finished_at"] else deps.clock.now()
    return {"seconds": session_seconds(deps, session, now)}
