import json
from datetime import timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.deps import AppDeps, get_deps
from app.errors import AppError
from app.exams import PASS_PERCENT, start_exam
from app.exercises import is_correct
from app.routes.exercises import MAX_GAP_SECONDS, shuffled_words

router = APIRouter()


class ExamAnswer(BaseModel):
    answer: str
    seconds: int = Field(default=0, ge=0)


def get_run(deps: AppDeps, run_id: int):
    run = deps.conn.execute("SELECT * FROM exam_runs WHERE id = ?", (run_id,)).fetchone()
    if run is None:
        raise AppError("exam_not_found", 404, "Prova não encontrada.")
    return run


def run_questions(deps: AppDeps, run) -> list:
    bank = {q.id: q for q in deps.content.exam(run["level"])}
    return [bank[i] for i in json.loads(run["question_ids"]) if i in bank]


def attempts_of(deps: AppDeps, run_id: int) -> dict:
    rows = deps.conn.execute("SELECT * FROM exam_attempts WHERE run_id = ?", (run_id,)).fetchall()
    return {r["question_id"]: r for r in rows}


@router.post("/exams/{level}/start")
def start(level: str, deps: AppDeps = Depends(get_deps)):
    run = get_run(deps, start_exam(deps, level))
    answered = attempts_of(deps, run["id"])
    questions = [{
        "id": q.id, "type": q.type, "prompt": q.prompt, "prompt_pt": q.prompt_pt, "glossary": q.glossary,
        "options": q.options, "words": shuffled_words(f"exam:{run['id']}:{q.id}", q.words),
        "answered": q.id in answered,
    } for q in run_questions(deps, run)]
    return {"run_id": run["id"], "level": run["level"], "questions": questions}


@router.post("/exams/runs/{run_id}/{question_id}/answer")
def answer(run_id: int, question_id: str, body: ExamAnswer, deps: AppDeps = Depends(get_deps)):
    run = get_run(deps, run_id)
    questions = {q.id: q for q in run_questions(deps, run)}
    question = questions.get(question_id)
    if question is None:
        raise AppError("question_not_found", 404, "Questão não está nesta prova.")
    now = deps.clock.now().astimezone(timezone.utc).isoformat()
    if run["finished_at"] is None:
        deps.conn.execute(
            "INSERT OR IGNORE INTO exam_attempts (run_id, question_id, answer, correct, seconds, day, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (run_id, question_id, body.answer, int(is_correct(question, body.answer)),
             min(body.seconds, MAX_GAP_SECONDS), deps.clock.today().isoformat(), now),
        )
        deps.conn.commit()
        attempts = attempts_of(deps, run_id)
        if len(attempts) >= len(questions):
            score = round(100 * sum(r["correct"] for r in attempts.values()) / len(questions))
            deps.conn.execute(
                "UPDATE exam_runs SET finished_at = ?, score = ?, passed = ? WHERE id = ? AND finished_at IS NULL",
                (now, score, int(score >= PASS_PERCENT), run_id))
            deps.conn.commit()
    run = get_run(deps, run_id)
    finished = run["finished_at"] is not None
    return {"saved": True, "finished": finished, "score": run["score"] if finished else None,
            "passed": bool(run["passed"]) if finished else None}


@router.get("/exams/runs/{run_id}")
def get_exam_run(run_id: int, deps: AppDeps = Depends(get_deps)):
    run = get_run(deps, run_id)
    finished = run["finished_at"] is not None
    results = None
    if finished:
        attempts = attempts_of(deps, run_id)
        results = []
        for q in run_questions(deps, run):
            a = attempts.get(q.id)
            results.append({
                "id": q.id, "prompt": q.prompt, "module_id": q.module_id,
                "module_title": deps.content.get(q.module_id).title,
                "user_answer": a["answer"] if a else None, "correct": bool(a and a["correct"]),
                "correct_answer": q.answers[0], "explanation": q.explanation,
            })
    return {"run_id": run["id"], "level": run["level"], "finished": finished, "score": run["score"],
            "passed": bool(run["passed"]) if finished else None, "pass_percent": PASS_PERCENT, "results": results}
