from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.ai.writing import new_writing_prompt, submit_writing
from app.deps import AppDeps, get_deps

router = APIRouter()


class SubmitBody(BaseModel):
    session_id: int
    text: str


@router.post("/writing/prompt")
def writing_prompt(deps: AppDeps = Depends(get_deps)):
    return new_writing_prompt(deps)


@router.post("/writing/submit")
def writing_submit(body: SubmitBody, deps: AppDeps = Depends(get_deps)):
    return submit_writing(deps, body.session_id, body.text)
