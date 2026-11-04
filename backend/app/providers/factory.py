from collections.abc import Callable

from app.config import Settings
from app.providers.base import Providers

PROFILES = {
    "free": {"chat": "gemini", "report": "gemini", "stt": "local", "tts": "local"},
    "paid": {"chat": "anthropic", "report": "anthropic", "stt": "openai", "tts": "openai"},
}
VALID = {
    "chat": {"gemini", "anthropic"},
    "report": {"gemini", "anthropic"},
    "stt": {"local", "openai"},
    "tts": {"local", "openai"},
}

Builder = Callable[[Settings], object]
# (role, name) -> builder. Real providers register themselves with lazy imports.
REGISTRY: dict[tuple[str, str], Builder] = {}


def resolve_names(settings: Settings) -> dict[str, str]:
    if settings.provider_profile not in PROFILES:
        raise ValueError(f"unknown PROVIDER_PROFILE: {settings.provider_profile!r}")
    names = dict(PROFILES[settings.provider_profile])
    overrides = {
        "chat": settings.chat_provider,
        "report": settings.report_provider,
        "stt": settings.stt_provider,
        "tts": settings.tts_provider,
    }
    for role, name in overrides.items():
        if name:
            names[role] = name
    for role, name in names.items():
        if name not in VALID[role]:
            raise ValueError(f"provider {name!r} is not valid for {role}")
    return names


def build_providers(settings: Settings) -> Providers:
    names = resolve_names(settings)
    built = {}
    for role in ("chat", "report", "stt", "tts"):
        builder = REGISTRY.get((role, names[role]))
        if builder is None:
            raise ValueError(f"provider {names[role]!r} for {role} is not available")
        built[role] = builder(settings)
    return Providers(**built)


# --- free providers (imports are lazy so missing SDKs only matter when selected) ---
def _gemini_chat(s: Settings):
    from app.providers.gemini import GeminiText

    return GeminiText(s.gemini_api_key, s.gemini_chat_model, thinking_level=s.gemini_chat_thinking,
                      fallback_model=s.gemini_fallback_model)


def _gemini_report(s: Settings):
    from app.providers.gemini import GeminiText

    return GeminiText(s.gemini_api_key, s.gemini_report_model, thinking_level=s.gemini_report_thinking,
                      fallback_model=s.gemini_fallback_model)


def _local_stt(s: Settings):
    from app.providers.local_stt import LocalWhisperStt

    return LocalWhisperStt(s.whisper_model_size, cpu_threads=s.whisper_cpu_threads)


def _local_tts(s: Settings):
    from app.providers.local_tts import LocalTts

    return LocalTts(s.piper_voice_path)


REGISTRY.update({
    ("chat", "gemini"): _gemini_chat,
    ("report", "gemini"): _gemini_report,
    ("stt", "local"): _local_stt,
    ("tts", "local"): _local_tts,
})


# --- paid providers ---
def _anthropic_chat(s: Settings):
    from app.providers.anthropic_provider import AnthropicText

    return AnthropicText(s.anthropic_api_key, s.anthropic_chat_model, s.anthropic_chat_effort, max_tokens=1024)


def _anthropic_report(s: Settings):
    from app.providers.anthropic_provider import AnthropicText

    return AnthropicText(s.anthropic_api_key, s.anthropic_report_model, s.anthropic_report_effort, max_tokens=4096)


def _openai_stt(s: Settings):
    from app.providers.openai_provider import OpenAIStt

    return OpenAIStt(s.openai_api_key, s.openai_stt_model)


def _openai_tts(s: Settings):
    from app.providers.openai_provider import OpenAITts

    return OpenAITts(s.openai_api_key, s.openai_tts_model, s.openai_tts_voice)


REGISTRY.update({
    ("chat", "anthropic"): _anthropic_chat,
    ("report", "anthropic"): _anthropic_report,
    ("stt", "openai"): _openai_stt,
    ("tts", "openai"): _openai_tts,
})
