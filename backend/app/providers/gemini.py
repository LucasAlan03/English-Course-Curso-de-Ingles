import time

from app.errors import ProviderAuthFailed, ProviderRateLimited, ProviderUnavailable
from app.providers.errors_map import is_auth_error, status_of
from app.providers.base import Msg, TextResult, Usage


class GeminiText:
    is_paid = False

    def __init__(self, api_key: str, model: str, client=None, sleep=time.sleep, retry_wait: float = 5.0):
        self.api_key = api_key
        self.model = model
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

        client = self._get_client()
        response = None
        for attempt in range(2):
            try:
                response = client.models.generate_content(model=self.model, contents=contents, config=config)
                break
            except Exception as exc:
                if is_auth_error(exc):
                    raise ProviderAuthFailed("gemini") from exc
                status = status_of(exc)
                rate_limited = status == 429 or "RESOURCE_EXHAUSTED" in str(exc)
                if not (rate_limited or (status is not None and status >= 500)):
                    raise
                if attempt == 0:
                    self._sleep(self._retry_wait)
                    continue
                raise (ProviderRateLimited if rate_limited else ProviderUnavailable)("gemini") from exc

        meta = getattr(response, "usage_metadata", None)
        usage = Usage(
            "gemini", self.model, "text",
            getattr(meta, "prompt_token_count", 0) or 0,
            getattr(meta, "candidates_token_count", 0) or 0,
        )
        return TextResult(response.text or "", usage)
