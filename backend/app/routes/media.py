import datetime as dt
import json
import re
import urllib.request
from urllib.parse import parse_qs, quote, urlparse
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator, model_validator

from app.db import insert
from app.deps import AppDeps, get_deps
from app.errors import AppError
from app.routes.words import add_word

router = APIRouter()

EPISODIC = {"series", "movie"}
MEDIA_COLUMNS = {"unit_minutes": "INTEGER", "count": "INTEGER", "url": "TEXT", "new_words": "TEXT"}
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
    minutes: int | None = Field(default=None, ge=1, le=1440)
    pages: int | None = Field(default=None, ge=1)
    unit_minutes: int | None = Field(default=None, ge=1, le=600)
    count: int | None = Field(default=None, ge=1, le=100)
    url: str | None = None
    new_words: str | None = None

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
        if self.category in EPISODIC:
            if self.unit_minutes is None or self.count is None:
                raise ValueError("series and movies need minutes per episode and a count")
            self.minutes = self.unit_minutes * self.count
        elif self.minutes is None:
            raise ValueError("minutes is required")
        return self


def _row(r) -> dict:
    return {k: r[k] for k in ("id", "date", "type", "category", "title", "episode", "minutes", "pages",
                              "unit_minutes", "count", "url", "new_words")}


def _save_new_words(deps: AppDeps, body: "MediaIn") -> None:
    if not body.new_words:
        return
    now = deps.clock.now().isoformat()
    for word in re.split(r"[,\n]", body.new_words):
        if word.strip():
            add_word(deps.conn, word.strip(), "", "", "", f"read:{body.title}", now)


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
        unit_minutes=body.unit_minutes, count=body.count, url=body.url, new_words=body.new_words,
        created_at=deps.clock.now().isoformat(),
    )
    _save_new_words(deps, body)
    return _row(_get(deps, item_id))


@router.get("/media")
def list_media(date: dt.date, deps: AppDeps = Depends(get_deps)):
    rows = deps.conn.execute("SELECT * FROM media_logs WHERE date = ? ORDER BY id", (date.isoformat(),)).fetchall()
    return [_row(r) for r in rows]


@router.put("/media/{item_id}")
def update_media(item_id: int, body: MediaIn, deps: AppDeps = Depends(get_deps)):
    _get(deps, item_id)
    deps.conn.execute(
        "UPDATE media_logs SET date = ?, type = ?, category = ?, title = ?, episode = ?, minutes = ?, pages = ?, "
        "unit_minutes = ?, count = ?, url = ?, new_words = ? WHERE id = ?",
        (body.date.isoformat(), body.type, body.category, body.title, body.episode, body.minutes, body.pages,
         body.unit_minutes, body.count, body.url, body.new_words, item_id),
    )
    deps.conn.commit()
    _save_new_words(deps, body)
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


_YT_ID = re.compile(r"^[A-Za-z0-9_-]{6,20}$")


def youtube_video_url(url: str) -> str | None:
    """Canonical watch URL for the usual YouTube link shapes, or None."""
    text = url.strip()
    if not text:
        return None
    if "://" not in text:
        text = "https://" + text
    parts = urlparse(text)
    host = (parts.hostname or "").lower().removeprefix("www.").removeprefix("m.")
    video_id = None
    if host == "youtu.be":
        video_id = parts.path.strip("/").split("/")[0]
    elif host == "youtube.com":
        if parts.path == "/watch":
            video_id = (parse_qs(parts.query).get("v") or [None])[0]
        elif parts.path.startswith("/shorts/"):
            video_id = parts.path.split("/")[2]
    if video_id and _YT_ID.match(video_id):
        return f"https://www.youtube.com/watch?v={video_id}"
    return None


def fetch_oembed(url: str) -> dict:
    with urllib.request.urlopen("https://www.youtube.com/oembed?format=json&url=" + quote(url, safe=""),
                                timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


@router.get("/media/youtube-title")
def youtube_title(url: str = ""):
    canonical = youtube_video_url(url)
    if canonical is None:
        return {"title": None}
    try:
        title = fetch_oembed(canonical).get("title")
    except Exception:  # offline, private video, bad JSON: the user types the title
        return {"title": None}
    return {"title": title if isinstance(title, str) and title.strip() else None}


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
