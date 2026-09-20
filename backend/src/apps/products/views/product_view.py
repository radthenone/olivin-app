from __future__ import annotations

from django.db.models import F, OuterRef, Prefetch, QuerySet, Subquery
from django.utils.translation import gettext_lazy
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import AllowAny
from rest_framework.settings import api_settings

from apps.inventory.models import has_available_variant
from apps.products.filters import MIN_PRICE, ProductFilterSet
from apps.products.models import EFFECTIVE_PRICE, Product, ProductVariant
from apps.products.schema import product_schema
from apps.products.serializers import ProductDetailSerializer, ProductListSerializer

ORDERING_FIELDS = {
    "price": F(MIN_PRICE).asc(nulls_last=True),
    "-price": F(MIN_PRICE).desc(nulls_last=True),
    "newest": F("created_at").desc(),
    "name": F("name").asc(),
    "-name": F("name").desc(),
}
DEFAULT_ORDERING = "newest"

# Produkt, którego nie da się kupić, schodzi na koniec listy przy **każdym**
# sortowaniu (`CONTEXT.md`, InventoryItem). Nie znika — wariant bez stanu
# zostaje widoczny jako niedostępny.
HAS_AVAILABLE = "has_available_variant"


class ProductOrderingFilter(OrderingFilter):
    """Sortowanie po nazwach z listy, nie po nazwach kolumn.

    `?ordering=price` musi zadziałać, choć „cena" nie jest kolumną produktu,
    tylko adnotacją z najtańszego wariantu. Kolejność jest podana wprost jako
    wyrażenie, bo produkt bez wariantów ma tę adnotację pustą, a puste wartości
    PostgreSQL i SQLite układają w przeciwnych miejscach.
    """

    # `gettext_lazy`, bo DRF deklaruje to pole jako tekst leniwy — zwykły
    # łańcuch byłby niespójnym nadpisaniem.
    ordering_description = gettext_lazy(
        "Kolejność listy: price, -price, newest, name, -name. Domyślnie newest."
    )

    def get_valid_fields(self, queryset, view, context=None):
        return [(key, key) for key in ORDERING_FIELDS]

    def filter_queryset(self, request, queryset, view):
        requested = request.query_params.get(self.ordering_param) or DEFAULT_ORDERING
        expression = ORDERING_FIELDS.get(requested, ORDERING_FIELDS[DEFAULT_ORDERING])
        # Rozstrzygnięcie remisu identyfikatorem: bez niego strona druga
        # potrafi powtórzyć pozycję ze strony pierwszej.
        return queryset.order_by(F(HAS_AVAILABLE).desc(), expression, "-id")


@product_schema
class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """Katalog produktów dla sklepu.

    Actions:
    - list:     GET /products/         — opublikowane, każdy z najtańszym wariantem
    - retrieve: GET /products/{slug}/  — produkt z pełną listą wariantów

    Tylko odczyt: katalog prowadzi właściciel w panelu, nie API (ADR 0021).
    Szkic nie jest widoczny pod żadnym adresem — queryset go nie zawiera, więc
    wejście na adres szkicu kończy się tym samym 404 co adres nieistniejący.
    """

    permission_classes = [AllowAny]
    lookup_field = "slug"
    filterset_class = ProductFilterSet
    # Globalne backendy zostają (ADR/konwencje z #98); dochodzi sortowanie,
    # bo lista katalogu jest jedynym miejscem, które go potrzebuje.
    filter_backends = [
        *api_settings.DEFAULT_FILTER_BACKENDS,
        ProductOrderingFilter,
    ]

    def get_queryset(self) -> QuerySet[Product]:
        variants = (
            ProductVariant.objects.with_effective_price()
            .select_related("inventory")
            .prefetch_related("inventory__movements", "gemstones")
            .order_by(EFFECTIVE_PRICE, "sku")
        )
        cheapest = (
            ProductVariant.objects.with_effective_price()
            .filter(product=OuterRef("pk"))
            .order_by(EFFECTIVE_PRICE, "sku")
            .values(EFFECTIVE_PRICE)[:1]
        )
        return (
            Product.objects.published()
            .select_related("category")
            .prefetch_related(
                Prefetch("variants", queryset=variants),
                "images",
                "variants__images",
            )
            # Podzapytanie, a nie `Min()` po złączeniu: agregat liczyłby się
            # z wariantów już przyciętych filtrami cech, więc cena produktu
            # zmieniałaby się w zależności od tego, co jeszcze jest włączone.
            .annotate(**{MIN_PRICE: Subquery(cheapest)})
            .annotate(**{HAS_AVAILABLE: has_available_variant()})
        )

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ProductDetailSerializer
        return ProductListSerializer
