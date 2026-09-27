"""Przeliczenie koszyka na walutę kursu (ADR 0019).

Jedno miejsce liczy pozycje, grawer, rabat i dostawę w euro — z niego
korzysta podgląd koszyka i dostawy oraz składanie zamówienia, więc klient
płaci dokładnie tyle, ile zobaczył w kasie. Wejście jest zawsze w złotych
(ceny źródłowe); wynik w walucie kursu.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal
from typing import Any

from apps.orders.models import CartItem
from apps.orders.services.cart import CartTotals
from apps.products.models import ExchangeRate
from apps.products.pricing import (
    MetalRates,
    active_metal_rates,
    cost_floor,
    price_in,
    round_up_to_half,
)
from apps.promotions.models import PromotionKind
from apps.promotions.services import AppliedPromotion
from common.money import Money


@dataclass(frozen=True, slots=True)
class ConvertedLine:
    """Pozycja koszyka w walucie kursu — te same pola co `CartItem`."""

    unit_price: Money
    goods_price: Money
    engraving_unit_price: Money
    engraving_price: Money
    discount: Money

    @property
    def line_total(self) -> Money:
        return self.goods_price + self.engraving_price


def convert_shipping(cost: Money, rate: ExchangeRate) -> Money:
    """Dostawa w górę do centa — bez ,00/,50, bo to nie cena katalogowa."""
    return rate.convert(cost)


def convert_line(
    item: CartItem,
    applied: AppliedPromotion | None,
    rate: ExchangeRate,
    metal_rates: MetalRates | None = None,
) -> ConvertedLine:
    """Pozycja w euro; rabat liczony od linii w euro, nie przeliczony z PLN.

    Procent idzie od towaru w euro, kwota promocji (w złotych) jest
    przeliczana — obie w dół do centa. Rabat przycinany do progu kosztu
    przeliczonego w górę, więc towar po rabacie nie schodzi pod koszt.
    """
    variant = item.variant
    count = item.specimen_count * item.quantity
    unit = price_in(variant, rate, metal_rates)
    goods = unit * count
    zero = Money.zero(rate.currency)

    engraving_unit = zero
    engraving_pln = variant.product.engraving_price
    if engraving_pln is not None and item.engraving_text:
        engraving_unit = round_up_to_half(rate.convert(Money(engraving_pln)))

    discount = zero
    if applied is not None:
        promotion = applied.promotion
        if promotion.kind == PromotionKind.PERCENT:
            nominal = goods.multiply(
                Decimal(promotion.value) / Decimal(100), rounding=ROUND_FLOOR
            )
        else:
            nominal = rate.convert(
                Money(promotion.value, promotion.currency) * count,
                rounding=ROUND_FLOOR,
            )
        floor = cost_floor(variant, metal_rates)
        if floor is not None:
            headroom = goods - rate.convert(floor, rounding=ROUND_CEILING) * count
            discount = max(zero, min(nominal, headroom))

    return ConvertedLine(
        unit_price=unit,
        goods_price=goods,
        engraving_unit_price=engraving_unit,
        engraving_price=engraving_unit * count,
        discount=discount,
    )


def convert_cart(
    items: Iterable[CartItem],
    discounts: Mapping[Any, AppliedPromotion],
    rate: ExchangeRate,
) -> tuple[dict[Any, ConvertedLine], CartTotals]:
    """Pozycje i podsumowanie w walucie kursu.

    Kupon ma nominał w złotych (ADR 0011), więc w euro nic nie pokrywa —
    zamówienie w euro z kuponem jest odrzucane przy składaniu.
    """
    rows = list(items)
    metal_rates = active_metal_rates()
    lines = {
        item.pk: convert_line(item, discounts.get(item.pk), rate, metal_rates)
        for item in rows
    }
    zero = Money.zero(rate.currency)
    subtotal = sum((line.line_total for line in lines.values()), start=zero)
    discount = sum((line.discount for line in lines.values()), start=zero)
    return lines, CartTotals(
        item_count=len(rows),
        subtotal=subtotal,
        discount_amount=discount,
        coupon_amount=zero,
        total=subtotal - discount,
    )
