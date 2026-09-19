from __future__ import annotations

from django.db.models import Prefetch, QuerySet
from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from apps.products.models import EFFECTIVE_PRICE, Product, ProductVariant
from apps.products.schema import product_schema
from apps.products.serializers import ProductDetailSerializer, ProductListSerializer


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

    def get_queryset(self) -> QuerySet[Product]:
        variants = ProductVariant.objects.with_effective_price().order_by(
            EFFECTIVE_PRICE, "sku"
        )
        return (
            Product.objects.published()
            .select_related("category")
            .prefetch_related(Prefetch("variants", queryset=variants))
        )

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ProductDetailSerializer
        return ProductListSerializer
