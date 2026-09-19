from __future__ import annotations

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.products.models import Product, ProductVariant
from core.api.serializers import MoneySerializer


class ProductVariantSerializer(serializers.ModelSerializer):
    """Wariant widziany przez klienta.

    Cena jest tą, którą klient faktycznie zapłaci: ręczna ma pierwszeństwo
    przed wyliczoną (ADR 0022). Klient nie musi wiedzieć, która to która.
    """

    price = MoneySerializer(source="effective_price", read_only=True)

    class Meta:
        model = ProductVariant
        fields = [
            "id",
            "sku",
            "metal_color",
            "size",
            "length",
            "stone",
            "metal_weight_grams",
            "price",
            "vat_rate",
            "is_vat_exempt",
            "vat_exemption_basis",
        ]
        read_only_fields = fields


class ProductListSerializer(serializers.ModelSerializer):
    """Produkt na liście — reprezentuje go najtańszy wariant (`CONTEXT.md`)."""

    category = serializers.SlugRelatedField(
        slug_field="slug",
        read_only=True,
        help_text="Slug kategorii-liścia, do której należy produkt",
    )
    cheapest_variant = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "category",
            "material",
            "fineness",
            "is_made_to_order",
            "production_time_days",
            "cheapest_variant",
        ]
        read_only_fields = fields

    @extend_schema_field(ProductVariantSerializer(allow_null=True))
    def get_cheapest_variant(self, obj: Product) -> dict | None:
        """Najtańszy wariant z już wczytanej listy — bez zapytania na produkt.

        Widok wstawia warianty posortowane po cenie skutecznej, więc pierwszy
        z nich jest najtańszy. Produkt bez wariantów nie jest błędem: do czasu
        dodania pierwszego wariantu nie ma czego wycenić.
        """
        variants = list(obj.variants.all())  # type: ignore[missing-attribute]
        if not variants:
            return None
        return ProductVariantSerializer(variants[0], context=self.context).data


class ProductDetailSerializer(serializers.ModelSerializer):
    """Strona produktu — pełna lista wariantów."""

    category = serializers.SlugRelatedField(
        slug_field="slug",
        read_only=True,
        help_text="Slug kategorii-liścia, do której należy produkt",
    )
    variants = ProductVariantSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "category",
            "material",
            "fineness",
            "is_made_to_order",
            "production_time_days",
            "variants",
        ]
        read_only_fields = fields
