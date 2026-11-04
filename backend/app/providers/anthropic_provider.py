from app.errors import InvalidAIOutput
from app.providers.base import Msg, TextResult, Usage
from app.providers.errors_map import classify


class AnthropicText:
    is_paid = True

    def __init__(self, api_key: str, model: str, effort: str = "", max_tokens: int = 1024, client=None):
        self.api_key = api_key
        self.model = model
        self.effort = effort
        self.max_tokens = max_tokens
        self._client = client

    def _get_client(self):
        if self._client is None:
            import anthropic  # imported lazily: only needed when actually used

            self._client = anthropic.Anthropic(api_key=self.api_key)
        return self._client

    def generate(self, system: str, messages: list[Msg], json_mode: bool = False) -> TextResult:
        # json_mode needs no special handling: the prompts already ask for JSON only.
        kwargs = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": system,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }
        if self.effort:
            kwargs["output_config"] = {"effort": self.effort}
        try:
            response = self._get_client().messages.create(**kwargs)
        except Exception as exc:
            mapped = classify(exc, "anthropic")
            if mapped:
                raise mapped from exc
            raise
        if response.stop_reason == "refusal":
            raise InvalidAIOutput()
        text = "".join(b.text for b in response.content if getattr(b, "type", None) == "text")
        usage = Usage("anthropic", self.model, "text", response.usage.input_tokens, response.usage.output_tokens)
        return TextResult(text, usage)
