from typing import Literal

from fastapi import APIRouter, Depends, File, Form, UploadFile
from pydantic import BaseModel

from app.ai.conversation import run_turn
from app.ai.report import finish_session
from app.db import insert
from app.deps import AppDeps, get_deps
from app.errors import AppError
from app.sessions_repo import get_session

router = APIRouter()


class CreateSession(BaseModel):
    kind: Literal["lesson", "review", "free", "writing"]
    module_id: str | None = None
    topic: str | None = None


@router.post("/sessions")
def create_session(body: CreateSession, deps: AppDeps = Depends(get_deps)):
    if body.kind in ("lesson", "review"):
        if not body.module_id:
            raise AppError("module_required", 422, "Escolha um módulo.")
        try:
            deps.content.get(body.module_id)
        except KeyError:
            raise AppError("module_not_found", 404, "Módulo não encontrado.")
    session_id = insert(
        deps.conn, "sessions", kind=body.kind, module_id=body.module_id, topic=body.topic,
        started_at=deps.clock.now().isoformat(),
    )
    return {"id": session_id}


@router.post("/sessions/{session_id}/turn")
async def session_turn(
    session_id: int,
    text: str | None = Form(None),
    audio: UploadFile | None = File(None),
    want_audio: bool = Form(False),
    deps: AppDeps = Depends(get_deps),
):
    session = get_session(deps.conn, session_id)
    data = await audio.read() if audio is not None else None
    mime = (audio.content_type if audio is not None else None) or "audio/webm"
    return run_turn(deps, session, text, data, mime, want_audio)


@router.post("/sessions/{session_id}/finish")
def session_finish(session_id: int, deps: AppDeps = Depends(get_deps)):
    return finish_session(deps, get_session(deps.conn, session_id))
