import secrets
import sqlite3
from dataclasses import dataclass

from fastapi import Request

from app.clock import Clock
from app.config import Settings
from app.content import ContentRepo
from app.providers.base import Providers
from app.usage import UsageTracker


@dataclass
class AppDeps:
    """Everything a route or service needs; built once in create_app."""

    settings: Settings
    clock: Clock
    conn: sqlite3.Connection
    providers: Providers
    content: ContentRepo
    tracker: UsageTracker


def token_is_valid(given: str | None, expected: str) -> bool:
    return bool(given) and secrets.compare_digest(given, expected)


def get_deps(request: Request) -> AppDeps:
    return request.app.state.deps
