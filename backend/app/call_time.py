"""Minutes spent in conversation: app sessions (active time) plus calls logged by hand."""

from datetime import date, datetime, timedelta

from app.deps import AppDeps

GAP_CAP_SECONDS = 180
CALL_KINDS = ("lesson", "review", "free", "teach")


def active_seconds(times: list[datetime], cap: int = GAP_CAP_SECONDS) -> int:
    ordered = sorted(times)
    return int(sum(min((b - a).total_seconds(), cap) for a, b in zip(ordered, ordered[1:])))


def _events(deps: AppDeps, session, now: datetime | None = None) -> list[datetime]:
    rows = deps.conn.execute("SELECT created_at FROM messages WHERE session_id = ?", (session["id"],)).fetchall()
    events = [datetime.fromisoformat(session["started_at"])] + [datetime.fromisoformat(r["created_at"]) for r in rows]
    if session["finished_at"]:
        events.append(datetime.fromisoformat(session["finished_at"]))
    if now is not None:
        events.append(now)
    return events


def session_seconds(deps: AppDeps, session, now: datetime | None = None) -> int:
    return active_seconds(_events(deps, session, now))


def app_seconds_for_day(deps: AppDeps, day: date) -> int:
    # Look a day around the local date in UTC, then keep the sessions whose local start date is `day`.
    low = (day - timedelta(days=1)).isoformat()
    high = (day + timedelta(days=2)).isoformat()
    marks = ",".join("?" for _ in CALL_KINDS)
    rows = deps.conn.execute(
        f"SELECT * FROM sessions WHERE kind IN ({marks}) AND started_at >= ? AND started_at < ?",
        (*CALL_KINDS, low, high),
    ).fetchall()
    total = 0
    for s in rows:
        if datetime.fromisoformat(s["started_at"]).astimezone(deps.clock.tz).date() != day:
            continue
        spoke = deps.conn.execute("SELECT 1 FROM messages WHERE session_id = ? AND role = 'user' LIMIT 1",
                                  (s["id"],)).fetchone()
        if spoke:
            total += session_seconds(deps, s)
    return total


def external_minutes(deps: AppDeps, start: date, end: date) -> int:
    return deps.conn.execute("SELECT COALESCE(SUM(minutes), 0) FROM call_logs WHERE date >= ? AND date <= ?",
                             (start.isoformat(), end.isoformat())).fetchone()[0]


def call_minutes_for_day(deps: AppDeps, day: date) -> int:
    return (app_seconds_for_day(deps, day) + external_minutes(deps, day, day) * 60) // 60
