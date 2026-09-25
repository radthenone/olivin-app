from __future__ import annotations

from rest_framework import serializers

from apps.products.models import EURO
from apps.shipping.models import ShippingMethodKind, ShippingZone
from common.money import DEFAULT_CURRENCY
from core.api.serializers import MoneySerializer


class ShippingMethodQuerySerializer(serializers.Serializer):
    """Parametry `GET /shipping-methods/`.

    Wartość koszyka rozstrzyga, które metody w ogóle wolno pokazać i ile
    kosztują, więc jest parametrem zapytania, a nie polem odpowiedzi. Brak
    wartości traktujemy jak pusty koszyk: klient oglądający stronę „Dostawa”
    ma zobaczyć pełen cennik, a nie błąd.
    """

    order_value = serializers.IntegerField(
        required=False,
        default=0,
        min_value=0,
        help_text="Wartość koszyka w groszach; domyślnie pusty koszyk",
    )
    zone = serializers.ChoiceField(
        choices=ShippingZone.choices,
        required=False,
        default=ShippingZone.PL,
        help_text="Strefa dostawy wynikająca z adresu klienta",
    )
    currency = serializers.ChoiceField(
        choices=[DEFAULT_CURRENCY, EURO],
        required=False,
        default=DEFAULT_CURRENCY,
        help_text=(
            "Waluta kosztu. `order_value` zawsze w groszach PLN; EUR przelicza "
            "koszt po bieżącym kursie, jak zamówienie do strefy EU (ADR 0019)."
        ),
    )


class ShippingOfferSerializer(serializers.Serializer):
    """Metoda dostawy z kosztem policzonym dla konkretnej wartości koszyka.

    Górna wartość zamówienia nie wychodzi na zewnątrz: klient nie ma jej po
    co znać, bo metoda, której limit przekroczył, po prostu nie ma go na
    liście. Ubezpieczenia też tu nie ma — jest wliczone w stawkę (ADR 0028).
    """

    id = serializers.UUIDField(source="method.id", read_only=True)
    name = serializers.CharField(source="method.name", read_only=True)
    # `ChoiceField`, a nie `CharField`: bez listy wartości schemat ogłasza goły
    # `string`, a wygenerowany klient traci typ, po którym kasa rozgałęzia się
    # na kod paczkomatu (ADR 0028).
    kind = serializers.ChoiceField(
        choices=ShippingMethodKind.choices,
        source="method.kind",
        read_only=True,
    )
    zone = serializers.ChoiceField(
        choices=ShippingZone.choices,
        source="method.zone",
        read_only=True,
    )
    cost = MoneySerializer(read_only=True)
    is_free = serializers.BooleanField(
        read_only=True,
        help_text=(
            "Czy klient nie zapłaci za tę dostawę — z progu darmowej dostawy "
            "albo ze stawki zero, jak przy odbiorze osobistym"
        ),
    )
