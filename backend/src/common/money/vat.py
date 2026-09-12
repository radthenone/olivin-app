from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from common.money.money import Money


@dataclass(frozen=True, slots=True)
class VatBreakdown:
    """Kwota brutto rozbita na netto i podatek. Zawsze `net + tax == gross`."""

    gross: Money
    net: Money
    tax: Money


def split_gross(gross: Money, rate: Decimal) -> VatBreakdown:
    """Wylicza netto i podatek z ceny brutto (Price w słowniku jest brutto).

    `rate` to ułamek, np. `Decimal("0.23")`. Zaokrąglane jest netto, raz,
    ROUND_HALF_UP; podatek to różnica, więc rozbicie zawsze sumuje się do brutto.
    Stawka 0 (zwolnienie) daje podatek zero bez specjalnego przypadku.
    """
    if isinstance(rate, float):
        raise TypeError("rate must be Decimal, not float")
    if rate < 0:
        raise ValueError("rate must be non-negative")

    net_amount = (Decimal(gross.amount) / (Decimal(1) + rate)).quantize(
        Decimal(1), rounding=ROUND_HALF_UP
    )
    net = Money(int(net_amount), gross.currency)
    return VatBreakdown(gross=gross, net=net, tax=gross - net)
