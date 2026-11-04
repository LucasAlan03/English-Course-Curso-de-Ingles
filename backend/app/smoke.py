from app.providers.base import Msg, Providers
from app.usage import UsageTracker

Result = tuple[str, bool, str]


def _text_check(name: str, model, tracker: UsageTracker) -> Result:
    try:
        tracker.ensure_can_spend(model.is_paid)
        reply = model.generate("Reply with the single word OK.", [Msg("user", "Say OK.")])
        tracker.record(reply.usage)
        return name, bool(reply.text.strip()), reply.text.strip()[:60] or "empty reply"
    except Exception as exc:
        return name, False, str(exc)


def run_smoke(providers: Providers, tracker: UsageTracker) -> list[Result]:
    """One real call to each provider of the active profile. Never stops at the first failure."""
    results: dict[str, Result] = {
        "chat": _text_check("chat", providers.chat, tracker),
        "report": _text_check("report", providers.report, tracker),
    }

    audio = None
    try:
        tracker.ensure_can_spend(providers.tts.is_paid)
        speech = providers.tts.synthesize("Hello, this is a test.")
        tracker.record(speech.usage)
        audio = speech
        results["tts"] = ("tts", bool(speech.audio), f"{len(speech.audio)} bytes of {speech.mime}")
    except Exception as exc:
        results["tts"] = ("tts", False, str(exc))

    if audio is None:
        results["stt"] = ("stt", False, "skipped: the TTS step produced no audio to transcribe")
    else:
        try:
            tracker.ensure_can_spend(providers.stt.is_paid)
            heard = providers.stt.transcribe(audio.audio, audio.mime)
            tracker.record(heard.usage)
            ok = "hello" in heard.text.lower()
            results["stt"] = ("stt", ok, f'heard: "{heard.text.strip()}"')
        except Exception as exc:
            results["stt"] = ("stt", False, str(exc))

    return [results[name] for name in ("chat", "report", "stt", "tts")]
