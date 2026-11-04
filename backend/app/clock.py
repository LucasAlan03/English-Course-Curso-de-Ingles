from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo


class Clock:
    def __init__(self, tz: str):
        self.tz = ZoneInfo(tz)

    def now(self) -> datetime:
        raise NotImplementedError

    def today(self) -> date:
        return self.now().astimezone(self.tz).date()


class SystemClock(Clock):
    def now(self) -> datetime:
        return datetime.now(timezone.utc)


class FixedClock(Clock):
    def __init__(self, now: datetime, tz: str):
        super().__init__(tz)
        self._now = now

    def now(self) -> datetime:
        return self._now
