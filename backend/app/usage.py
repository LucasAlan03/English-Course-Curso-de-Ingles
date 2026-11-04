import sqlite3
from datetime import datetime, timezone

from app.clock import Clock
from app.config import Settings
from app.db import insert
from app.errors import MonthlyCapReached
from app.pricing import cost_brl
from app.providers.base import Usage


class UsageTracker:
    def __init__(self, conn: sqlite3.Connection, settings: Settings, clock: Clock):
        self.conn = conn
        self.settings = settings
        self.clock = clock

    def record(self, usage: Usage) -> float:
        cost = cost_brl(usage)
        insert(
            self.conn, "api_usage",
            provider=usage.provider, model=usage.model, kind=usage.kind,
            input_units=usage.input_units, output_units=usage.output_units,
            cost_brl=cost, created_at=self.clock.now().astimezone(timezone.utc).isoformat(),
        )
        return cost

    def _month_bounds_utc(self) -> tuple[str, str]:
        today = self.clock.today()
        start = datetime(today.year, today.month, 1, tzinfo=self.clock.tz)
        nxt = (today.year + (today.month == 12), today.month % 12 + 1)
        end = datetime(nxt[0], nxt[1], 1, tzinfo=self.clock.tz)
        as_utc = lambda d: d.astimezone(timezone.utc).isoformat()
        return as_utc(start), as_utc(end)

    def month_total_brl(self) -> float:
        start, end = self._month_bounds_utc()
        row = self.conn.execute(
            "SELECT COALESCE(SUM(cost_brl), 0) FROM api_usage WHERE created_at >= ? AND created_at < ?",
            (start, end),
        ).fetchone()
        return float(row[0])

    def status(self) -> dict:
        total = self.month_total_brl()
        s = self.settings
        level = "blocked" if total >= s.monthly_cap_brl else "warn" if total >= s.monthly_warn_brl else "ok"
        return {"total": total, "warn": s.monthly_warn_brl, "cap": s.monthly_cap_brl, "level": level}

    def ensure_can_spend(self, is_paid: bool) -> None:
        if is_paid and self.month_total_brl() >= self.settings.monthly_cap_brl:
            raise MonthlyCapReached()
