"""Cost estimation. Prices are USD per single unit (token / second / character).

Free providers always cost 0. Paid models get their entries in PRICES when the paid
providers are added (prices checked against the official pricing pages then).
"""
from app.providers.base import Usage

USD_BRL = 5.5  # rough exchange rate used only for the monthly estimate

FREE_PROVIDERS = {"gemini", "local", "fake"}

# (provider, model, kind) -> (usd per input unit, usd per output unit)
PRICES: dict[tuple[str, str, str], tuple[float, float]] = {}


def per_million(usd: float) -> float:
    return usd / 1_000_000


def cost_brl(usage: Usage) -> float:
    if usage.provider in FREE_PROVIDERS:
        return 0.0
    in_rate, out_rate = PRICES[(usage.provider, usage.model, usage.kind)]
    return (usage.input_units * in_rate + usage.output_units * out_rate) * USD_BRL
