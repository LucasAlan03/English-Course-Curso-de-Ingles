from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/usage/month")
def usage_month(request: Request):
    return request.app.state.deps.tracker.status()
