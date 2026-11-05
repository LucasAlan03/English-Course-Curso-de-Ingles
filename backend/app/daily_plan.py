"""The guided study day: 7 blocks whose state is computed from the day's records."""

from datetime import date, datetime, timedelta

from app.call_time import call_minutes_for_day
from app.content import EXERCISE_COUNT
from app.deps import AppDeps

BLOCKS = ("grammar", "music", "call1", "watch", "read", "call2", "anki")
TITLES = {"grammar": "Gramática", "music": "Música", "call1": "Ligação 1", "watch": "Assistir", "read": "Ler",
          "call2": "Ligação 2", "anki": "Anki"}
TARGETS = {"grammar": 20, "call1": 10, "watch": 45, "read": 40, "call2": 10}
STREAK_LIMIT = 366


def _grammar(deps: AppDeps, day: date) -> tuple[bool, int]:
    d = day.isoformat()
    seconds = deps.conn.execute("SELECT COALESCE(SUM(seconds), 0) FROM exercise_attempts WHERE day = ?",
                                (d,)).fetchone()[0]
    seconds += deps.conn.execute("SELECT COALESCE(SUM(seconds), 0) FROM exam_attempts WHERE day = ?",
                                 (d,)).fetchone()[0]
    module_done = deps.conn.execute(
        "SELECT 1 FROM exercise_attempts WHERE kind = 'lesson' GROUP BY module_id "
        "HAVING COUNT(*) >= ? AND MAX(day) = ? LIMIT 1", (EXERCISE_COUNT, d)).fetchone() is not None
    exam_done = any(
        datetime.fromisoformat(r["finished_at"]).astimezone(deps.clock.tz).date() == day
        for r in deps.conn.execute("SELECT finished_at FROM exam_runs WHERE finished_at IS NOT NULL "
                                   "AND finished_at >= ? AND finished_at < ?",
                                   ((day - timedelta(days=1)).isoformat(), (day + timedelta(days=2)).isoformat()))
    )
    minutes = seconds // 60
    return module_done or exam_done or minutes >= TARGETS["grammar"], minutes


def _music(deps: AppDeps, day: date) -> bool:
    d = day.isoformat()
    final = deps.conn.execute("SELECT 1 FROM song_practice WHERE kind = 'final' AND day = ? LIMIT 1",
                              (d,)).fetchone()
    if final:
        return True
    row = deps.conn.execute(
        "SELECT 1 FROM song_practice WHERE chunk_id IS NOT NULL AND kind IN ('dictation', 'shadow') "
        "GROUP BY chunk_id HAVING COUNT(DISTINCT kind) = 2 AND MAX(day) = ? LIMIT 1", (d,)).fetchone()
    return row is not None


def _media_minutes(deps: AppDeps, day: date, kind: str) -> int:
    return deps.conn.execute("SELECT COALESCE(SUM(minutes), 0) FROM media_logs WHERE date = ? AND type = ?",
                             (day.isoformat(), kind)).fetchone()[0]


def _state(deps: AppDeps, day: date) -> dict[str, dict]:
    rows = deps.conn.execute("SELECT block, skipped, checked FROM day_state WHERE date = ?",
                             (day.isoformat(),)).fetchall()
    return {r["block"]: {"skipped": bool(r["skipped"]), "checked": bool(r["checked"])} for r in rows}


def day_plan(deps: AppDeps, day: date) -> dict:
    state = _state(deps, day)
    grammar_done, grammar_minutes = _grammar(deps, day)
    calls = call_minutes_for_day(deps, day)
    watch, read = _media_minutes(deps, day, "watch"), _media_minutes(deps, day, "read")
    facts = {
        "grammar": (grammar_done, grammar_minutes),
        "music": (_music(deps, day), None),
        "call1": (calls >= 10, min(calls, 10)),
        "watch": (watch >= TARGETS["watch"], watch),
        "read": (read >= TARGETS["read"], read),
        "call2": (calls >= 20, min(max(calls - 10, 0), 10)),
        "anki": (state.get("anki", {}).get("checked", False), None),
    }
    blocks, current = [], None
    for key in BLOCKS:
        done, minutes = facts[key]
        if done:
            status = "done"
        elif state.get(key, {}).get("skipped"):
            status = "skipped"
        elif current is None:
            status, current = "current", key
        else:
            status = "pending"
        blocks.append({"key": key, "title": TITLES[key], "status": status, "minutes": minutes,
                       "target": TARGETS.get(key)})
    return {"date": day.isoformat(), "blocks": blocks, "current": current,
            "complete": all(b["status"] == "done" for b in blocks)}


def streak(deps: AppDeps, today: date) -> int:
    """Consecutive complete days ending today, or yesterday when today is not complete yet."""
    day = today if day_plan(deps, today)["complete"] else today - timedelta(days=1)
    count = 0
    while count < STREAK_LIMIT and day_plan(deps, day)["complete"]:
        count += 1
        day -= timedelta(days=1)
    return count
