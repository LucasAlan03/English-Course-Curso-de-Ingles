import datetime as dt
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator, model_validator

from app.db import insert
from app.deps import AppDeps, get_deps
from app.errors import AppError

router = APIRouter()

CATEGORIES = {
    "watch": {"series", "movie", "video", "podcast"},
    "read": {"hq", "book", "article", "other"},
}


class MediaIn(BaseModel):
    date: dt.date
    type: Literal["watch", "read"]
    category: str
    title: str
    episode: str | None = None
    minutes: int = Field(ge=1, le=1440)
    pages: int | None = Field(default=None, ge=1)

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("title is required")
        return value

    @model_validator(mode="after")
    def category_matches_type(self):
        if self.category not in CATEGORIES[self.type]:
            raise ValueError(f"category {self.category!r} is not valid for {self.type}")
        return self


def _row(r) -> dict:
    return {k: r[k] for k in ("id", "date", "type", "category", "title", "episode", "minutes", "pages")}


def _get(deps: AppDeps, item_id: int):
    row = deps.conn.execute("SELECT * FROM media_logs WHERE id = ?", (item_id,)).fetchone()
    if row is None:
        raise AppError("media_not_found", 404, "Registro não encontrado.")
    return row


@router.post("/media")
def create_media(body: MediaIn, deps: AppDeps = Depends(get_deps)):
    item_id = insert(
        deps.conn, "media_logs", date=body.date.isoformat(), type=body.type, category=body.category,
        title=body.title, episode=body.episode, minutes=body.minutes, pages=body.pages,
        created_at=deps.clock.now().isoformat(),
    )
    return _row(_get(deps, item_id))


@router.get("/media")
def list_media(date: dt.date, deps: AppDeps = Depends(get_deps)):
    rows = deps.conn.execute("SELECT * FROM media_logs WHERE date = ? ORDER BY id", (date.isoformat(),)).fetchall()
    return [_row(r) for r in rows]


@router.put("/media/{item_id}")
def update_media(item_id: int, body: MediaIn, deps: AppDeps = Depends(get_deps)):
    _get(deps, item_id)
    deps.conn.execute(
        "UPDATE media_logs SET date = ?, type = ?, category = ?, title = ?, episode = ?, minutes = ?, pages = ? "
        "WHERE id = ?",
        (body.date.isoformat(), body.type, body.category, body.title, body.episode, body.minutes, body.pages, item_id),
    )
    deps.conn.commit()
    return _row(_get(deps, item_id))


@router.delete("/media/{item_id}")
def delete_media(item_id: int, deps: AppDeps = Depends(get_deps)):
    _get(deps, item_id)
    deps.conn.execute("DELETE FROM media_logs WHERE id = ?", (item_id,))
    deps.conn.commit()
    return {"deleted": item_id}


def _totals(deps: AppDeps, start: dt.date, end: dt.date) -> dict:
    rows = deps.conn.execute(
        "SELECT type, category, minutes FROM media_logs WHERE date >= ? AND date <= ?",
        (start.isoformat(), end.isoformat()),
    ).fetchall()
    by_type: dict[str, int] = {}
    by_category: dict[str, int] = {}
    for r in rows:
        by_type[r["type"]] = by_type.get(r["type"], 0) + r["minutes"]
        by_category[r["category"]] = by_category.get(r["category"], 0) + r["minutes"]
    return {"total_minutes": sum(by_type.values()), "by_type": by_type, "by_category": by_category}


@router.get("/media/summary")
def media_summary(date: dt.date | None = None, deps: AppDeps = Depends(get_deps)):
    day = date or deps.clock.today()
    monday = day - dt.timedelta(days=day.weekday())
    first = day.replace(day=1)
    last = (first + dt.timedelta(days=32)).replace(day=1) - dt.timedelta(days=1)
    return {
        "day": _totals(deps, day, day),
        "week": _totals(deps, monday, monday + dt.timedelta(days=6)),
        "month": _totals(deps, first, last),
    }
