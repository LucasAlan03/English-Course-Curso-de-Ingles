"""Entry point for uvicorn:  uvicorn app.server:app_factory --factory --host 0.0.0.0 --port 8000"""
import logging
import threading

from fastapi import FastAPI

from app.config import Settings
from app.main import create_app
from app.providers.base import Providers

log = logging.getLogger("english")


def warm_up(providers: Providers) -> None:
    """Load the local voice models now, so the first conversation does not wait for them."""
    for provider in (providers.stt, providers.tts):
        hook = getattr(provider, "warm_up", None)
        if hook is None:
            continue
        try:
            hook()
        except Exception as exc:  # a missing model must not stop the server
            log.warning("warm-up failed for %s: %s", type(provider).__name__, exc)


def app_factory() -> FastAPI:
    settings = Settings()
    app = create_app(settings)
    if settings.warm_up:
        threading.Thread(target=warm_up, args=(app.state.deps.providers,), daemon=True, name="warm-up").start()
    return app
