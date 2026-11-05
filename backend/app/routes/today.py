from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.daily_plan import BLOCKS, day_plan, streak
from app.deps import AppDeps, get_deps
from app.errors import AppError

router = APIRouter()


class AnkiBody(BaseModel):
    checked: bool


def _set(deps: AppDeps, block: str, column: str, value: int) -> None:
    if block not in BLOCKS:
        raise AppError("unknown_block", 400, "Bloco desconhecido.")
    day = deps.clock.today().isoformat()
    deps.conn.execute("INSERT OR IGNORE INTO day_state (date, block, skipped, checked) VALUES (?, ?, 0, 0)",
                      (day, block))
    deps.conn.execute(f"UPDATE day_state SET {column} = ? WHERE date = ? AND block = ?", (value, day, block))
    deps.conn.commit()


def today_body(deps: AppDeps) -> dict:
    today = deps.clock.today()
    return {**day_plan(deps, today), "streak": streak(deps, today)}


@router.get("/today")
def get_today(deps: AppDeps = Depends(get_deps)):
    return today_body(deps)


@router.post("/today/{block}/skip")
def skip(block: str, deps: AppDeps = Depends(get_deps)):
    _set(deps, block, "skipped", 1)
    return today_body(deps)


@router.post("/today/{block}/unskip")
def unskip(block: str, deps: AppDeps = Depends(get_deps)):
    _set(deps, block, "skipped", 0)
    return today_body(deps)


@router.post("/today/anki")
def anki(body: AnkiBody, deps: AppDeps = Depends(get_deps)):
    _set(deps, "anki", "checked", int(body.checked))
    return today_body(deps)
