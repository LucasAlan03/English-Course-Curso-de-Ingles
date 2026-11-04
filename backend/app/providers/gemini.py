import time

from app.errors import ProviderAuthFailed, ProviderRateLimited, ProviderUnavailable
from app.providers.base import Msg, TextResult, Usage
from app.providers.errors_map import is_auth_error, status_of


class GeminiText:
    is_paid = False

    def __init__(
        self,
        api_key: str,
        model: str,
        client=None,
        sleep=time.sleep,
        retry_wait: float = 1.5,
        thinking_level: str = "",
        fallback_model: str = "",
    ):
        self.api_key = api_key
        self.model = model
        self.thinking_level = thinking_level
        self.fallback_model = fallback_model
        self._client = client
        self._sleep = sleep
        self._retry_wait = retry_wait

    def _get_client(self):
        if self._client is None:
            from google import genai  # imported lazily: only needed when actually used

            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def generate(self, system: str, messages: list[Msg], json_mode: bool = False) -> TextResult:
        contents = [
            {"role": "model" if m.role == "assistant" else "user", "parts": [{"text": m.content}]}
            for m in messages
        ]
        config: dict = {"system_instruction": system}
        if json_mode:
            config["response_mime_type"] = "application/json"
        if self.thinking_level:  # less "thinking" means much faster answers for short tasks
            config["thinking_config"] = {"thinking_level": self.thinking_level}

        client = self._get_client()
        models = [self.model]
        if self.fallback_model and self.fallback_model != self.model:
            models.append(self.fallback_model)  # used only when the main model stays overloaded

        response, used, rate_limited = None, self.model, False
        for index, name in enumerate(models):
            attempts = 2 if index == 0 else 1
            for attempt in range(attempts):
                try:
                    response = client.models.generate_content(model=name, contents=contents, config=config)
                    used = name
                    break
                except Exception as exc:
                    if is_auth_error(exc):
                        raise ProviderAuthFailed("gemini") from exc
                    status = status_of(exc)
                    rate_limited = status == 429 or "RESOURCE_EXHAUSTED" in str(exc)
                    if not (rate_limited or (status is not None and status >= 500)):
                        raise
                    if attempt + 1 < attempts:
                        self._sleep(self._retry_wait)
            if response is not None:
                break
        if response is None:
            raise (ProviderRateLimited if rate_limited else ProviderUnavailable)("gemini")

        meta = getattr(response, "usage_metadata", None)
        usage = Usage(
            "gemini", used, "text",
            getattr(meta, "prompt_token_count", 0) or 0,
            getattr(meta, "candidates_token_count", 0) or 0,
        )
        return TextResult(response.text or "", usage)
