from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.clock import Clock, SystemClock
from app.config import Settings
from app.deps import AppDeps, token_is_valid


def create_app(settings: Settings, *, providers=None, clock: Clock | None = None) -> FastAPI:
    app = FastAPI(title="English App")
    clock = clock or SystemClock(settings.tz)
    app.state.deps = AppDeps(settings=settings, clock=clock)

    @app.middleware("http")
    async def require_token(request: Request, call_next):
        if request.url.path != "/health" and not token_is_valid(
            request.headers.get("X-API-Token"), settings.api_token
        ):
            return JSONResponse({"error": "unauthorized", "detail": ""}, status_code=401)
        return await call_next(request)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
