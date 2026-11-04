from app.errors import AppError, ProviderAuthFailed, ProviderOutOfCredit, ProviderRateLimited, ProviderUnavailable

_AUTH_PHRASES = (
    "api key not valid", "api_key_invalid", "no api key was provided", "invalid x-api-key", "incorrect api key",
)


def status_of(exc: Exception) -> int | None:
    for attr in ("status_code", "code"):
        value = getattr(exc, attr, None)
        if isinstance(value, int):
            return value
    return None


def is_auth_error(exc: Exception) -> bool:
    return status_of(exc) in (401, 403) or any(p in str(exc).lower() for p in _AUTH_PHRASES)


def classify(exc: Exception, provider: str) -> AppError | None:
    """Turn a paid-provider SDK exception into an app error, or None if it is something else.

    Duck-typed on the status code and the message so it works for every SDK.
    """
    status = status_of(exc)
    message = str(exc).lower()
    if status == 402 or "credit balance" in message or "insufficient_quota" in message:
        return ProviderOutOfCredit(provider)
    if status == 429:
        return ProviderRateLimited(provider)
    if is_auth_error(exc):
        return ProviderAuthFailed(provider)
    if status is not None and status >= 500:  # includes Anthropic's 529 "overloaded"
        return ProviderUnavailable(provider)
    return None
