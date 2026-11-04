from app.errors import AppError, ProviderOutOfCredit, ProviderRateLimited


def classify(exc: Exception, provider: str) -> AppError | None:
    """Turn a paid-provider SDK exception into an app error, or None if it is something else.

    Duck-typed on `status_code` and the message so it works for every SDK.
    """
    status = getattr(exc, "status_code", None)
    message = str(exc).lower()
    if status == 402 or "credit balance" in message or "insufficient_quota" in message:
        return ProviderOutOfCredit(provider)
    if status == 429:
        return ProviderRateLimited(provider)
    return None
