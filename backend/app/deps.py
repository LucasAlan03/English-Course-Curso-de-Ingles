import secrets
from dataclasses import dataclass

from app.clock import Clock
from app.config import Settings


@dataclass
class AppDeps:
    """Everything a route or service needs; built once in create_app."""

    settings: Settings
    clock: Clock


def token_is_valid(given: str | None, expected: str) -> bool:
    return bool(given) and secrets.compare_digest(given, expected)
