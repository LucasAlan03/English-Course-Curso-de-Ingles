import hashlib
import json
import random
from datetime import timezone

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.audio import find_audio
from app.content import EXERCISE_COUNT, Exercise
from app.deps import AppDeps, get_deps
from app.errors import AppError
from app.exercises import is_correct, pick_review
from app.reviews import exercise_audio_name, schedule_review

router = APIRouter()
MAX_GAP_SECONDS = 180


class AnswerBody(BaseModel):
    answer: str
    seconds: int = Field(default=0, ge=0)
    run_id: int | None = None


class ReportBody(BaseModel):
    note: str = ""


def module_exercises(deps: AppDeps, module_id: str) -> list[Exercise]:
    try:
        deps.content.get(module_id)
    except KeyError:
        raise AppError("module_not_found", 404, "Módulo não encontrado.")
    return deps.content.exercises(module_id)


def find_exercise(deps: AppDeps, module_id: str, exercise_id: str) -> Exercise:
    for e in module_exercises(deps, module_id):
        if e.id == exercise_id:
            return e
    raise AppError("exercise_not_found", 404, "Exercício não encontrado.")


def shuffled_words(seed_text: str, words: list[str] | None) -> list[str] | None:
    if not words:
        return None
    seed = int(hashlib.sha256(seed_text.encode()).hexdigest()[:8], 16)
    shuffled = list(words)
    random.Random(seed).shuffle(shuffled)
    return shuffled


def item_view(module_id: str, e: Exercise, attempt=None) -> dict:
    result = None
    if attempt is not None:
        result = {"correct": bool(attempt["correct"]), "user_answer": attempt["answer"],
                  "correct_answer": e.answers[0], "explanation": e.explanation}
    return {
        "id": e.id, "block": e.block, "type": e.type, "prompt": e.prompt, "prompt_pt": e.prompt_pt,
        "glossary": e.glossary, "options": e.options, "words": shuffled_words(f"{module_id}:{e.id}", e.words),
        "audio_url": f"/audio/{exercise_audio_name(module_id, e.id)}" if e.audio_text else None,
        "answered": attempt is not None, "result": result,
    }


def lesson_attempts(deps: AppDeps, module_id: str) -> dict:
    rows = deps.conn.execute(
        "SELECT * FROM exercise_attempts WHERE module_id = ? AND kind = 'lesson'", (module_id,)).fetchall()
    return {r["exercise_id"]: r for r in rows}


@router.get("/modules/{module_id}/exercises")
def list_exercises(module_id: str, deps: AppDeps = Depends(get_deps)):
    exercises = module_exercises(deps, module_id)
    attempts = lesson_attempts(deps, module_id)
    return [item_view(module_id, e, attempts.get(e.id)) for e in exercises]


def save_attempt(deps: AppDeps, module_id: str, e: Exercise, answer: str, seconds: int,
                 kind: str = "lesson", run_id: int | None = None) -> bool:
    """Store the first answer only; return the stored correctness."""
    deps.conn.execute(
        "INSERT OR IGNORE INTO exercise_attempts (module_id, exercise_id, kind, run_id, answer, correct, seconds, "
        "day, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (module_id, e.id, kind, run_id, answer, int(is_correct(e, answer)), min(seconds, MAX_GAP_SECONDS),
         deps.clock.today().isoformat(), deps.clock.now().astimezone(timezone.utc).isoformat()),
    )
    deps.conn.commit()
    if kind == "lesson":
        row = deps.conn.execute("SELECT correct FROM exercise_attempts WHERE kind = 'lesson' AND module_id = ? "
                                "AND exercise_id = ?", (module_id, e.id)).fetchone()
    else:
        row = deps.conn.execute("SELECT correct FROM exercise_attempts WHERE kind = 'review' AND run_id = ? "
                                "AND exercise_id = ?", (run_id, e.id)).fetchone()
    return bool(row["correct"])


@router.post("/exercises/{module_id}/{exercise_id}/answer")
def answer_exercise(module_id: str, exercise_id: str, body: AnswerBody, deps: AppDeps = Depends(get_deps)):
    e = find_exercise(deps, module_id, exercise_id)
    response = {"correct_answer": e.answers[0], "explanation": e.explanation,
                "module_completed": False, "score": None, "next_due": None}
    if body.run_id is not None:
        return answer_review(deps, module_id, e, body, response)
    was_complete = len(lesson_attempts(deps, module_id)) >= EXERCISE_COUNT
    response["correct"] = save_attempt(deps, module_id, e, body.answer, body.seconds)
    attempts = lesson_attempts(deps, module_id)
    if not was_complete and len(attempts) >= EXERCISE_COUNT:
        score = round(100 * sum(r["correct"] for r in attempts.values()) / len(attempts))
        response.update(module_completed=True, score=score, next_due=schedule_review(deps, module_id, score))
    return response


def answer_review(deps: AppDeps, module_id: str, e: Exercise, body: AnswerBody, response: dict) -> dict:
    run = deps.conn.execute("SELECT * FROM review_runs WHERE id = ? AND module_id = ?",
                            (body.run_id, module_id)).fetchone()
    if run is None:
        raise AppError("review_not_found", 404, "Revisão não encontrada.")
    ids = json.loads(run["exercise_ids"])
    if e.id not in ids:
        raise AppError("exercise_not_found", 404, "Exercício não está nesta revisão.")
    response["correct"] = save_attempt(deps, module_id, e, body.answer, body.seconds, "review", run["id"])
    rows = deps.conn.execute("SELECT correct FROM exercise_attempts WHERE kind = 'review' AND run_id = ?",
                             (run["id"],)).fetchall()
    if run["finished_at"] is None and len(rows) >= len(ids):
        score = round(100 * sum(r["correct"] for r in rows) / len(ids))
        claimed = deps.conn.execute(
            "UPDATE review_runs SET finished_at = ?, score = ? WHERE id = ? AND finished_at IS NULL",
            (deps.clock.now().astimezone(timezone.utc).isoformat(), score, run["id"])).rowcount
        deps.conn.commit()
        if claimed:
            response.update(module_completed=True, score=score, next_due=schedule_review(deps, module_id, score))
    return response


@router.post("/reviews/{module_id}/start")
def start_review(module_id: str, deps: AppDeps = Depends(get_deps)):
    exercises = module_exercises(deps, module_id)
    if not exercises:
        raise AppError("no_exercises", 404, "Este módulo ainda não tem exercícios.")
    picked = pick_review(deps.conn, module_id, exercises)
    cur = deps.conn.execute(
        "INSERT INTO review_runs (module_id, exercise_ids, started_at) VALUES (?, ?, ?)",
        (module_id, json.dumps([e.id for e in picked]), deps.clock.now().astimezone(timezone.utc).isoformat()))
    deps.conn.commit()
    return {"run_id": cur.lastrowid, "exercises": [item_view(module_id, e) for e in picked]}


@router.post("/exercises/{module_id}/{exercise_id}/report")
def report_exercise(module_id: str, exercise_id: str, body: ReportBody, deps: AppDeps = Depends(get_deps)):
    find_exercise(deps, module_id, exercise_id)
    deps.conn.execute(
        "INSERT INTO exercise_reports (module_id, exercise_id, note, created_at) VALUES (?, ?, ?, ?)",
        (module_id, exercise_id, body.note, deps.clock.now().astimezone(timezone.utc).isoformat()),
    )
    deps.conn.commit()
    return {"ok": True}


@router.get("/audio/{name}")
def get_audio(name: str, deps: AppDeps = Depends(get_deps)):
    found = find_audio(deps.settings.data_dir, name)
    if found is None:
        raise AppError("audio_not_found", 404, "Áudio não encontrado.")
    path, media_type = found
    return FileResponse(path, media_type=media_type)
