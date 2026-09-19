from __future__ import annotations

import django_filters
from django.db.models import QuerySet

from apps.categories.models import Category
from apps.products.models import (
    Fineness,
    Length,
    Material,
    MetalColor,
    Product,
    RingSize,
    Stone,
)
from apps.products.search import search

MIN_PRICE = "min_price"


class ProductFilterSet(django_filters.FilterSet):
    """Zawężanie listy produktów parametrami `GET /products/`.

    Cechy wariantu (kolor kruszcu, rozmiar, długość, kamień) filtrują przez
    złączenie, więc produkt z kilkoma pasującymi wariantami wróciłby wielokrotnie
    — stąd `distinct` na każdym z tych filtrów.

    Cena idzie po adnotacji `min_price`, czyli po najtańszym wariancie
    produktu, a nie po złączeniu: złączenie zmieniałoby wynik w zależności od
    tego, które jeszcze filtry są włączone.
    """

    material = django_filters.ChoiceFilter(
        choices=Material.choices,
        label="Kruszec",
    )
    fineness = django_filters.ChoiceFilter(
        choices=Fineness.choices,
        label="Próba kruszcu",
    )
    metal_color = django_filters.ChoiceFilter(
        choices=MetalColor.choices,
        field_name="variants__metal_color",
        distinct=True,
        label="Kolor kruszcu",
    )
    stone = django_filters.ChoiceFilter(
        choices=Stone.choices,
        field_name="variants__stone",
        distinct=True,
        label="Rodzaj kamienia",
    )
    size = django_filters.ChoiceFilter(
        choices=RingSize.choices,
        field_name="variants__size",
        distinct=True,
        label="Rozmiar pierścionka",
    )
    length = django_filters.ChoiceFilter(
        choices=Length.choices,
        field_name="variants__length",
        distinct=True,
        label="Długość w centymetrach",
    )
    price_min = django_filters.NumberFilter(
        field_name=MIN_PRICE,
        lookup_expr="gte",
        label="Cena najtańszego wariantu od (grosze)",
    )
    price_max = django_filters.NumberFilter(
        field_name=MIN_PRICE,
        lookup_expr="lte",
        label="Cena najtańszego wariantu do (grosze)",
    )
    category = django_filters.CharFilter(
        method="filter_category",
        label="Slug kategorii; obejmuje również jej podkategorie",
    )
    search = django_filters.CharFilter(
        method="filter_search",
        label="Fraza szukana w nazwie i opisie",
    )

    class Meta:
        model = Product
        fields: list[str] = []

    def filter_category(
        self, queryset: QuerySet[Product], name: str, value: str
    ) -> QuerySet[Product]:
        return queryset.filter(category_id__in=Category.subtree_ids(value))

    def filter_search(
        self, queryset: QuerySet[Product], name: str, value: str
    ) -> QuerySet[Product]:
        return search(queryset, value)
