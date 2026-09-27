"""Wzór ceny wariantu (ADR 0022).

    cena = zaokrąglij_w_górę_do_złotówki(
        (masa_kruszcu × kurs_za_gram + suma_składników_kosztu) × marża
    )

Marża pochodzi z wariantu, a jeśli go tam nie ma — z kategorii produktu.
Cena ręczna, jeśli jest ustawiona, ma pierwszeństwo przed wynikiem wzoru
i nie jest przez przeliczenie dotykana.

Próg kosztowy (`cost_floor`) to ten sam rachunek bez marży. Ani cena ręczna,
ani promocja nie schodzą poniżej niego.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal

from apps.products.models.exchange_rate import ExchangeRate
from apps.products.models.metal_rate import MetalRate
from apps.products.models.variant import ProductVariant
from common.money import DEFAULT_CURRENCY, Money

# Cena kończy się na pełnych złotówkach — grosze w cenie katalogowej
# biżuterii nie niosą informacji, a psują odbiór.
GROSZE_IN_ZLOTY = 100
# Cena w euro kończy się na ,00 albo ,50 (ADR 0019, uzupełnienie 2026-09-22).
HALF_UNIT = 50


@dataclass(frozen=True, slots=True)
class Margin:
    """Narzut: procentowy albo kwotowy, nigdy oba naraz."""

    percent: Decimal | None = None
    amount: Money | None = None

    @property
    def is_empty(self) -> bool:
        return self.percent is None and self.amount is None

    def apply(self, cost: Money) -> Money:
        if self.percent is not None:
            return cost.multiply(Decimal(1) + self.percent / Decimal(100))
        if self.amount is not None:
            return cost + self.amount
        return cost


EMPTY_MARGIN = Margin()

# Aktywne kursy kruszców wczytane raz: (kruszec, próba) → kurs.
MetalRates = Mapping[tuple[str, str], MetalRate]


def margin_for(variant: ProductVariant) -> Margin:
    """Narzut wariantu, a w jego braku narzut kategorii produktu.

    Nadpisanie działa na poziomie całego narzutu, nie pojedynczego pola:
    wariant z narzutem kwotowym nie dziedziczy procentu z kategorii, bo
    złożenie dwóch narzutów nie jest tym, o co prosi ADR 0022.
    """
    if variant.margin_percent is not None:
        return Margin(percent=variant.margin_percent)
    if variant.margin_amount is not None:
        return Margin(amount=Money(variant.margin_amount, variant.currency))

    category = variant.product.category
    if category.margin_percent is not None:
        return Margin(percent=category.margin_percent)
    if category.margin_amount is not None:
        return Margin(amount=Money(category.margin_amount, DEFAULT_CURRENCY))
    return EMPTY_MARGIN


def metal_component(variant: ProductVariant, rate: MetalRate) -> Money:
    """Masa kruszcu razy kurs za gram, zaokrąglone dokładnie raz."""
    return rate.price.multiply(variant.metal_weight_grams, rounding=ROUND_HALF_UP)


def components_total(variant: ProductVariant) -> Money:
    total = Money.zero(variant.currency)
    # Stuby nie generują odwrotnej relacji zadeklarowanej `related_name`.
    for component in variant.cost_components.all():  # type: ignore[missing-attribute]
        total = total + component.money
    return total


def active_metal_rates() -> dict[tuple[str, str], MetalRate]:
    """Wszystkie aktywne kursy kruszców jednym zapytaniem — dla list wariantów."""
    return {(rate.metal, rate.fineness): rate for rate in MetalRate.objects.active()}


def active_rate_for(
    variant: ProductVariant, metal_rates: MetalRates | None = None
) -> MetalRate | None:
    if metal_rates is not None:
        product = variant.product
        return metal_rates.get((product.material, product.fineness))
    return MetalRate.objects.active_for(
        variant.product.material, variant.product.fineness
    )


def cost_floor(
    variant: ProductVariant, metal_rates: MetalRates | None = None
) -> Money | None:
    """Koszt wariantu bez marży (`CONTEXT.md`, Cost floor).

    `None`, gdy nie ma aktywnego kursu dla kruszcu i próby produktu — wtedy
    składnika kruszcowego nie da się policzyć, a zgadywanie progu dałoby
    liczbę wyglądającą na prawdziwą.
    """
    rate = active_rate_for(variant, metal_rates)
    if rate is None:
        return None
    return metal_component(variant, rate) + components_total(variant)


def round_up_to_zloty(amount: Money) -> Money:
    grosze = (Decimal(amount.amount) / Decimal(GROSZE_IN_ZLOTY)).to_integral_value(
        rounding=ROUND_CEILING
    ) * GROSZE_IN_ZLOTY
    return Money(int(grosze), amount.currency)


def calculate_price(variant: ProductVariant) -> Money | None:
    """Cena wyliczona ze wzoru albo `None`, gdy brak aktywnego kursu."""
    floor = cost_floor(variant)
    if floor is None:
        return None
    return round_up_to_zloty(margin_for(variant).apply(floor))


def round_up_to_half(amount: Money) -> Money:
    """W górę do najbliższej końcówki ,00 albo ,50."""
    halves = (Decimal(amount.amount) / Decimal(HALF_UNIT)).to_integral_value(
        rounding=ROUND_CEILING
    )
    return Money(int(halves) * HALF_UNIT, amount.currency)


def price_in(
    variant: ProductVariant,
    rate: ExchangeRate,
    metal_rates: MetalRates | None = None,
) -> Money:
    """Cena wariantu w walucie kursu (ADR 0019).

    Przeliczona i zaokrąglona w górę do ,00/,50, ale nigdy poniżej kosztu
    wariantu przeliczonego tym samym kursem — próg z ADR 0022 obowiązuje
    w każdej walucie.
    """
    price = round_up_to_half(rate.convert(variant.effective_price))
    floor = cost_floor(variant, metal_rates)
    if floor is None:
        return price
    return max(price, round_up_to_half(rate.convert(floor)))
