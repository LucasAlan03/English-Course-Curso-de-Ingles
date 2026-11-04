from fastapi import APIRouter, Depends, File, UploadFile

from app.deps import AppDeps, get_deps
from app.errors import EmptyTranscript
from app.speech import heard_words

router = APIRouter()


@router.post("/stt")
async def speech_to_text(audio: UploadFile = File(...), deps: AppDeps = Depends(get_deps)):
    """Transcribe a recording. Used by the app's voice test and to check the microphone setup."""
    data = await audio.read()
    deps.tracker.ensure_can_spend(deps.providers.stt.is_paid)
    result = deps.providers.stt.transcribe(data, audio.content_type or "audio/webm")
    deps.tracker.record(result.usage)
    text = result.text.strip()
    if not heard_words(text):
        raise EmptyTranscript()
    return {"text": text}
