from __future__ import annotations

from dataclasses import dataclass

from django.conf import settings

from apps.shipping.models import ShippingMethod
from common.money import DEFAULT_CURRENCY, CurrencyMismatchError, Money


@dataclass(frozen=True, slots=True)
class ShippingOffer:
    """Metoda dostawy wraz z kosztem policzonym dla konkretnego koszyka.

    Koszt nie jest polem metody, bo zależy od wartości zamówienia: ta sama
    metoda bywa płatna i darmowa. Krok trzeci kasy dostaje gotową kwotę,
    więc klient widzi pełną sumę przed intencją płatniczą (ADR 0030).
    """

    method: ShippingMethod
    cost: Money

    @property
    def is_free(self) -> bool:
        return not self.cost


def free_shipping_threshold(currency: str = DEFAULT_CURRENCY) -> Money | None:
    """Wartość zamówienia, od której dostawa nic nie kosztuje.

    Jeden próg dla całego sklepu (`CONTEXT.md`, ShippingMethod), trzymany jako
    ustawienie `FREE_SHIPPING_THRESHOLD` — nie jako model. To jedna liczba,
    wspólna dla wszystkich procesów, bez historii i bez wariantów; model
    wymagałby wymuszenia jedynego wiersza i ekranu w panelu dla pojedynczej
    kwoty. `None` wyłącza darmową dostawę.
    """
    amount = getattr(settings, "FREE_SHIPPING_THRESHOLD", None)
    if amount is None:
        return None
    return Money(int(amount), currency)


def cost_for(method: ShippingMethod, order_value: Money) -> Money:
    """Koszt metody dla danej wartości koszyka: stawka albo zero od progu.

    Próg zadziała „od kwoty”, nie „powyżej kwoty” — zamówienie dokładnie za
    tyle, ile wynosi próg, ma dostawę gratis. Tak brzmi obietnica „darmowa
    dostawa od 500 zł” i tak klient ją czyta.
    """
    _reject_currency_mismatch(method, order_value)
    threshold = free_shipping_threshold(order_value.currency)
    if threshold is not None and order_value >= threshold:
        return Money.zero(method.currency)
    return method.rate_money


def available_methods(*, order_value: Money, zone: str) -> list[ShippingOffer]:
    """Metody, które klient może dziś wybrać dla koszyka o tej wartości.

    Odsiewane jest wszystko, czego klient nie może wybrać: metoda wygaszona,
    metoda z innej strefy i metoda, której górna wartość zamówienia została
    przekroczona (ADR 0028). Odbiór osobisty limitu nie ma, więc zostaje
    zawsze — bez osobnego wyjątku, bo ograniczenie w bazie nie pozwala mu
    limitu nadać.
    """
    if order_value.amount < 0:
        raise ValueError("order_value must not be negative")

    methods = (
        ShippingMethod.objects.active()
        .for_zone(zone)
        .within_value_limit(order_value)
        .order_by("rate", "name")
    )
    return [
        ShippingOffer(method=method, cost=cost_for(method, order_value))
        for method in methods
    ]


def _reject_currency_mismatch(method: ShippingMethod, order_value: Money) -> None:
    """Koszyk i stawka muszą być w jednej walucie — inaczej suma jest fikcją.

    Dziś stawki są złotowe, a sprzedaż do Unii w euro dołoży przeliczenie
    (ADR 0019). Do tego czasu niezgodność ma być głośna, a nie cicho
    zignorowana.
    """
    if method.currency != order_value.currency:
        raise CurrencyMismatchError(f"{method.currency} vs {order_value.currency}")
