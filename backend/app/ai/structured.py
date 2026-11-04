import json
import re
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from app.errors import InvalidAIOutput
from app.providers.base import Msg, TextModel
from app.usage import UsageTracker

T = TypeVar("T", bound=BaseModel)

_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)
_RETRY_HINT = (
    "Your previous answer was not valid JSON for the requested schema. "
    "Reply again with valid JSON only."
)


def _parse(text: str, schema: type[T]) -> T:
    match = _FENCE.search(text)
    raw = match.group(1) if match else text
    return schema.model_validate(json.loads(raw.strip()))


def generate_structured(
    model: TextModel, system: str, messages: list[Msg], schema: type[T], tracker: UsageTracker
) -> T:
    """Ask for JSON matching `schema`; retry once on invalid output, then give up."""
    attempt_messages = list(messages)
    for attempt in range(2):
        tracker.ensure_can_spend(model.is_paid)
        result = model.generate(system, attempt_messages, json_mode=True)
        tracker.record(result.usage)
        try:
            return _parse(result.text, schema)
        except (ValueError, ValidationError):  # JSONDecodeError is a ValueError
            if attempt == 0:
                attempt_messages = attempt_messages + [Msg("user", _RETRY_HINT)]
    raise InvalidAIOutput()
