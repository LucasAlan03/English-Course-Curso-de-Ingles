from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.clock import Clock, SystemClock
from app.config import Settings
import os

from app.content import ContentRepo
from app.db import connect, init_schema
from app.deps import AppDeps, token_is_valid
from app.errors import AppError
from app.providers.factory import build_providers
from app.routes import listening as listening_routes
from app.routes import modules as modules_routes
from app.routes import sessions as sessions_routes
from app.routes import usage as usage_routes
from app.usage import UsageTracker


def create_app(settings: Settings, *, providers=None, clock: Clock | None = None) -> FastAPI:
    app = FastAPI(title="English App")
    clock = clock or SystemClock(settings.tz)
    conn = connect(os.path.join(settings.data_dir, "app.db"))
    init_schema(conn)
    app.state.deps = AppDeps(
        settings=settings,
        clock=clock,
        conn=conn,
        providers=providers or build_providers(settings),
        content=ContentRepo.load(settings.content_dir),
        tracker=UsageTracker(conn, settings, clock),
    )

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        return JSONResponse(exc.body(), status_code=exc.status)

    app.include_router(usage_routes.router)
    app.include_router(listening_routes.router)
    app.include_router(sessions_routes.router)
    app.include_router(modules_routes.router)

    @app.middleware("http")
    async def require_token(request: Request, call_next):
        path = request.url.path
        token = request.headers.get("X-API-Token")
        if not token and path.startswith("/audio/"):
            token = request.query_params.get("token")  # audio players cannot send headers
        if path != "/health" and not token_is_valid(token, settings.api_token):
            return JSONResponse({"error": "unauthorized", "detail": ""}, status_code=401)
        return await call_next(request)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
