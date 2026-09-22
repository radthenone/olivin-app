from __future__ import annotations

from dataclasses import dataclass

from django.conf import settings

from apps.shipping.models import ShippingMethod
from common.money import DEFAULT_CURRENCY, Money


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
        """Czy klient nie zapłaci za tę dostawę — z progu albo ze stawki zero.

        Odbiór osobisty jest darmowy przy każdej wartości koszyka, bo nic nie
        jedzie przewoźnikiem; nie ma powodu, żeby klient widział go inaczej
        niż kuriera puszczonego gratis powyżej progu.
        """
        return not self.cost


def free_shipping_threshold() -> Money | None:
    """Wartość zamówienia, od której dostawa nic nie kosztuje.

    Jeden próg dla całego sklepu (`CONTEXT.md`, ShippingMethod), trzymany jako
    ustawienie `FREE_SHIPPING_THRESHOLD` — nie jako model. To jedna liczba,
    wspólna dla wszystkich procesów, bez historii i bez wariantów; model
    wymagałby wymuszenia jedynego wiersza i ekranu w panelu dla pojedynczej
    kwoty. `None` wyłącza darmową dostawę.

    Kwota jest w walucie źródłowej sklepu — ceny powstają w złotych i dopiero
    z nich bierze się euro (ADR 0019). Progu nie parametryzujemy walutą, bo
    jedna liczba stemplowana dowolnym kodem waluty znaczyłaby raz 500 zł,
    a raz 500 €.
    """
    amount = getattr(settings, "FREE_SHIPPING_THRESHOLD", None)
    if amount is None:
        return None
    return Money(int(amount), DEFAULT_CURRENCY)


def cost_for(method: ShippingMethod, order_value: Money) -> Money:
    """Koszt metody dla danej wartości koszyka: stawka albo zero od progu.

    Próg zadziała „od kwoty”, nie „powyżej kwoty” — zamówienie dokładnie za
    tyle, ile wynosi próg, ma dostawę gratis. Tak brzmi obietnica „darmowa
    dostawa od 500 zł” i tak klient ją czyta.

    Metoda i koszyk muszą być w jednej walucie — pilnuje tego `available_methods`,
    które metod w obcej walucie w ogóle nie wypuszcza.
    """
    threshold = free_shipping_threshold()
    if threshold is not None and threshold.currency == order_value.currency:
        if order_value >= threshold:
            return Money.zero(method.currency)
    return method.rate_money


def available_methods(*, order_value: Money, zone: str) -> list[ShippingOffer]:
    """Metody, które klient może dziś wybrać dla koszyka o tej wartości.

    Odsiewane jest wszystko, czego klient nie może wybrać: metoda wygaszona,
    metoda z innej strefy, metoda wyceniona w innej walucie niż koszyk
    i metoda, której górna wartość zamówienia została przekroczona
    (ADR 0028). Odbiór osobisty limitu nie ma, więc zostaje zawsze — bez
    osobnego wyjątku, bo ograniczenie w bazie nie pozwala mu limitu nadać.

    Niezgodność waluty jest filtrem, a nie wyjątkiem: to publiczny odczyt dla
    każdego, więc jeden wiersz wpisany w panelu nie może zamieniać go w 500.
    Przeliczanie stawek na walutę klienta przyjdzie z ADR 0019.
    """
    if order_value.amount < 0:
        raise ValueError("order_value must not be negative")

    methods = (
        ShippingMethod.objects.active()
        .for_zone(zone)
        .in_currency(order_value.currency)
        .within_value_limit(order_value)
        .order_by("rate", "name")
    )
    return [
        ShippingOffer(method=method, cost=cost_for(method, order_value))
        for method in methods
    ]
