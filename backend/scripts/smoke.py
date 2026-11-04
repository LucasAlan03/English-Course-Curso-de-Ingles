"""Makes one real call to each provider of the active profile and prints OK / FAIL for each.

    python scripts/smoke.py

Run it after filling in .env. With PROVIDER_PROFILE=paid this spends a few cents.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.clock import SystemClock  # noqa: E402
from app.config import Settings  # noqa: E402
from app.db import connect, init_schema  # noqa: E402
from app.providers.factory import build_providers, resolve_names  # noqa: E402
from app.smoke import run_smoke  # noqa: E402
from app.usage import UsageTracker  # noqa: E402


def main() -> int:
    settings = Settings()
    names = resolve_names(settings)
    print(f"Profile: {settings.provider_profile}  providers: {names}")
    conn = connect(os.path.join(settings.data_dir, "app.db"))
    init_schema(conn)
    tracker = UsageTracker(conn, settings, SystemClock(settings.tz))
    failed = 0
    for name, ok, message in run_smoke(build_providers(settings), tracker):
        print(f"[{'OK' if ok else 'FAIL'}] {name:7} {message}")
        failed += 0 if ok else 1
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
