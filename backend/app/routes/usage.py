from fastapi import APIRouter, Depends

from app.deps import AppDeps, get_deps
from app.providers.factory import resolve_names

router = APIRouter()


@router.get("/usage/month")
def usage_month(deps: AppDeps = Depends(get_deps)):
    return deps.tracker.status()


@router.get("/settings")
def current_settings(deps: AppDeps = Depends(get_deps)):
    """Which providers are active (never the keys), plus this month's spend."""
    return {
        "profile": deps.settings.provider_profile,
        "providers": resolve_names(deps.settings),
        "usage": deps.tracker.status(),
    }
