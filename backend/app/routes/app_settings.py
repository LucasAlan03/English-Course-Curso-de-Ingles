import json
import re

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator

from app.deps import AppDeps, get_deps

router = APIRouter()

DEFAULT_REMINDERS = ["19:00", "21:00"]
_HHMM = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


class Reminders(BaseModel):
    times: list[str] = Field(max_length=4)

    @field_validator("times")
    @classmethod
    def valid_times(cls, value: list[str]) -> list[str]:
        for t in value:
            if not _HHMM.match(t):
                raise ValueError(f"invalid time {t!r}, use HH:MM")
        return value


def _get(deps: AppDeps, key: str):
    row = deps.conn.execute("SELECT value FROM app_settings WHERE key = ?", (key,)).fetchone()
    return json.loads(row["value"]) if row else None


@router.get("/settings/reminders")
def get_reminders(deps: AppDeps = Depends(get_deps)):
    return {"times": _get(deps, "reminders") or DEFAULT_REMINDERS}


@router.put("/settings/reminders")
def put_reminders(body: Reminders, deps: AppDeps = Depends(get_deps)):
    deps.conn.execute("INSERT OR REPLACE INTO app_settings (key, value) VALUES ('reminders', ?)",
                      (json.dumps(body.times),))
    deps.conn.commit()
    return {"times": body.times}
