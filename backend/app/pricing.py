"""Cost estimation. Prices are USD per single unit (token / second / character).

Free providers always cost 0. These are ESTIMATES for the monthly cap, not an invoice:
the real balance lives in each provider's console.

Sources: Claude prices from the Anthropic API model table (checked 2026-11-03); OpenAI audio
prices from third-party summaries of OpenAI pricing (NOT confirmed on openai.com - re-check).
"""
from app.providers.base import Usage

USD_BRL = 5.5  # rough exchange rate used only for the monthly estimate

FREE_PROVIDERS = {"gemini", "local", "fake"}


def per_million(usd: float) -> float:
    return usd / 1_000_000


# (provider, model, kind) -> (usd per input unit, usd per output unit)
PRICES: dict[tuple[str, str, str], tuple[float, float]] = {
    ("anthropic", "claude-haiku-5-5", "text"): (per_million(0.10), per_million(0.50)),
    ("anthropic", "claude-sonnet-5-5", "text"): (per_million(2.00), per_million(10.00)),
    # STT units are seconds: 0.003 USD per minute.
    ("openai", "gpt-4o-mini-transcribe", "stt"): (0.003 / 60, 0.0),
    ("openai", "whisper-1", "stt"): (0.006 / 60, 0.0),
    # TTS units are characters: roughly 0.015 USD per minute of speech at ~900 characters per minute.
    ("openai", "gpt-4o-mini-tts", "tts"): (0.015 / 900, 0.0),
    ("openai", "tts-1", "tts"): (per_million(15.0), 0.0),
}


def _rates(usage: Usage) -> tuple[float, float]:
    exact = PRICES.get((usage.provider, usage.model, usage.kind))
    if exact:
        return exact
    # Unknown model (e.g. overridden in .env): assume the most expensive known one, so the
    # estimate errs on the safe side instead of crashing or reporting zero.
    same_kind = [rates for (p, _, k), rates in PRICES.items() if p == usage.provider and k == usage.kind]
    if not same_kind:
        raise KeyError((usage.provider, usage.model, usage.kind))
    return max(same_kind, key=lambda r: r[0] + r[1])


def cost_brl(usage: Usage) -> float:
    if usage.provider in FREE_PROVIDERS:
        return 0.0
    in_rate, out_rate = _rates(usage)
    return (usage.input_units * in_rate + usage.output_units * out_rate) * USD_BRL
