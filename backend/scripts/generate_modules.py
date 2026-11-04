"""Draft module files with the AI configured in .env (the report model of the active profile).

    python scripts/generate_modules.py              # only modules that have no file yet
    python scripts/generate_modules.py --only b1_futures --force
"""
import argparse
import os
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ai.module_content import generate_all  # noqa: E402
from app.clock import SystemClock  # noqa: E402
from app.config import BASE_DIR, Settings  # noqa: E402
from app.db import connect, init_schema  # noqa: E402
from app.providers.factory import build_providers  # noqa: E402
from app.usage import UsageTracker  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", help="generate just this module id")
    parser.add_argument("--force", action="store_true", help="overwrite existing files")
    args = parser.parse_args()

    settings = Settings()
    conn = connect(os.path.join(settings.data_dir, "app.db"))
    init_schema(conn)
    tracker = UsageTracker(conn, settings, SystemClock(settings.tz))
    model = build_providers(settings).report

    outline = yaml.safe_load((BASE_DIR / "content" / "curriculum.yaml").read_text(encoding="utf-8"))["modules"]
    written = generate_all(outline, settings.content_dir, model, tracker, settings.prompts_dir, args.only, args.force)
    print(f"Wrote {len(written)} module(s): {', '.join(written) or '-'}")
    print("Review the files in content/modules before studying them.")


if __name__ == "__main__":
    main()
