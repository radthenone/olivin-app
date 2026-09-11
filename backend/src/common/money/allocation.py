from __future__ import annotations

from collections.abc import Sequence

from common.money.money import Money


def allocate(total: Money, ratios: Sequence[int]) -> list[Money]:
    """Dzieli kwotę proporcjonalnie do wag tak, żeby części sumowały się dokładnie do całości.

    Każda część to podłoga z proporcji; reszta z dzielenia trafia w całości na
    ostatnią pozycję. To reguła z #44 — rabat rozbity na pozycje ma się zgadzać
    co do grosza z rabatem całkowitym, a miejsce, gdzie ląduje reszta, ma być
    przewidywalne.
    """
    if not ratios:
        raise ValueError("ratios must not be empty")
    if any(r < 0 for r in ratios):
        raise ValueError("ratios must be non-negative")
    weight = sum(ratios)
    if weight == 0:
        raise ValueError("ratios must not all be zero")

    # Ujemna całość (korekta, zwrot) dzieli się tak samo — na wartości bezwzględnej,
    # ze znakiem przywróconym na końcu, żeby podłoga nie ciągnęła w stronę -inf.
    sign = -1 if total.amount < 0 else 1
    magnitude = abs(total.amount)

    parts = [magnitude * r // weight for r in ratios]
    parts[-1] += magnitude - sum(parts)

    return [Money(sign * p, total.currency) for p in parts]


def split_evenly(total: Money, count: int) -> list[Money]:
    """Dzieli kwotę na `count` równych części; reszta na ostatnią."""
    if count <= 0:
        raise ValueError("count must be positive")
    return allocate(total, [1] * count)
