from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.ai.listening import generate_listening, is_correct, list_items
from app.audio import find_audio
from app.deps import AppDeps, get_deps
from app.errors import AppError
from app.sessions_repo import get_session

router = APIRouter()


class AnswerBody(BaseModel):
    answer: str


@router.get("/sessions/{session_id}/listening")
def session_listening(session_id: int, deps: AppDeps = Depends(get_deps)):
    session = get_session(deps.conn, session_id)
    if session["kind"] not in ("lesson", "review") or not session["module_id"]:
        raise AppError("invalid_session_kind", 400, "Só aulas e revisões têm listening.")
    if not list_items(deps.conn, session_id):
        count = 5 if session["kind"] == "lesson" else 3
        generate_listening(deps, session_id, session["module_id"], count)
    return list_items(deps.conn, session_id)


@router.post("/listening/{item_id}/answer")
def answer_item(item_id: int, body: AnswerBody, deps: AppDeps = Depends(get_deps)):
    row = deps.conn.execute("SELECT * FROM listening_items WHERE id = ?", (item_id,)).fetchone()
    if row is None:
        raise AppError("item_not_found", 404, "Exercício não encontrado.")
    if row["correct"] is None:  # the first answer counts
        correct = is_correct(row["answer"], body.answer)
        deps.conn.execute(
            "UPDATE listening_items SET user_answer = ?, correct = ? WHERE id = ?",
            (body.answer, int(correct), item_id),
        )
        deps.conn.commit()
    else:
        correct = bool(row["correct"])
    return {"correct": correct, "correct_answer": row["answer"], "explanation": row["explanation"]}


@router.get("/audio/{name}")
def get_audio(name: str, deps: AppDeps = Depends(get_deps)):
    found = find_audio(deps.settings.data_dir, name)
    if found is None:
        raise AppError("audio_not_found", 404, "Áudio não encontrado.")
    path, media_type = found
    return FileResponse(path, media_type=media_type)
