class AppError(Exception):
    def __init__(self, code: str, status: int, detail: str = "", **extra):
        super().__init__(detail or code)
        self.code = code
        self.status = status
        self.detail = detail
        self.extra = extra

    def body(self) -> dict:
        return {"error": self.code, "detail": self.detail, **self.extra}


class ProviderOutOfCredit(AppError):
    def __init__(self, provider: str):
        super().__init__(
            "provider_out_of_credit", 402,
            f"Os créditos de {provider} acabaram. Recarregue no console do provedor.",
            provider=provider,
        )


class ProviderRateLimited(AppError):
    def __init__(self, provider: str):
        super().__init__(
            "provider_rate_limited", 429,
            f"{provider} atingiu o limite de requisições. Aguarde um pouco ou ative o perfil pago.",
            provider=provider,
        )


class MonthlyCapReached(AppError):
    def __init__(self):
        super().__init__("monthly_cap_reached", 402, "O teto mensal de gastos foi atingido.")


class InvalidAIOutput(AppError):
    def __init__(self):
        super().__init__("invalid_ai_output", 502, "A IA devolveu uma resposta inválida. Tente de novo.")


class EmptyTranscript(AppError):
    def __init__(self):
        super().__init__("empty_transcript", 422, "Não consegui ouvir nada. Repita, por favor.")
