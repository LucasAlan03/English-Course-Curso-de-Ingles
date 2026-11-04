from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    api_token: str = "change-me"
    provider_profile: str = "free"  # free | paid
    tz: str = "America/Sao_Paulo"

    monthly_warn_brl: float = 45.0
    monthly_cap_brl: float = 50.0

    data_dir: str = str(BASE_DIR / "data")
    content_dir: str = str(BASE_DIR / "content" / "modules")
    prompts_dir: str = str(BASE_DIR / "prompts")

    gemini_api_key: str = ""
    gemini_chat_model: str = "gemini-3.5-flash-lite"
    gemini_report_model: str = "gemini-3.6-flash"
    whisper_model_size: str = "base"
    piper_voice_path: str = str(BASE_DIR / "data" / "voices" / "en_US-lessac-medium.onnx")
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    anthropic_chat_model: str = "claude-haiku-5-5"
    anthropic_report_model: str = "claude-sonnet-5-5"
    anthropic_chat_effort: str = "low"  # empty = do not send effort
    anthropic_report_effort: str = "medium"
    openai_stt_model: str = "gpt-4o-mini-transcribe"
    openai_tts_model: str = "gpt-4o-mini-tts"
    openai_tts_voice: str = "alloy"

    # Per-component overrides; empty means "use the profile default".
    chat_provider: str = ""
    report_provider: str = ""
    stt_provider: str = ""
    tts_provider: str = ""
