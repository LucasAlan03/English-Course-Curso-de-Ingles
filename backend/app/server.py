"""Entry point for uvicorn:  uvicorn app.server:app_factory --factory --host 0.0.0.0 --port 8000"""
from fastapi import FastAPI

from app.config import Settings
from app.main import create_app


def app_factory() -> FastAPI:
    return create_app(Settings())
