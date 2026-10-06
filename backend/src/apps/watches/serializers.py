from __future__ import annotations

from rest_framework import serializers

from apps.products.models import ProductVariant
from apps.watches.models import Watch, WatchKind


class WatchVariantSerializer(serializers.ModelSerializer):
    """Wariant w kontekście obserwowanych — tyle, ile potrzebuje przycisk."""

    effective_price = serializers.SerializerMethodField()
    available = serializers.SerializerMethodField()
    is_available = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = ["id", "sku", "effective_price", "available", "is_available"]
        read_only_fields = fields

    def get_effective_price(self, obj: ProductVariant) -> int:
        return obj.effective_price.amount

    def get_available(self, obj: ProductVariant) -> int | None:
        return obj.available

    def get_is_available(self, obj: ProductVariant) -> bool:
        return obj.is_available


class WatchSerializer(serializers.ModelSerializer):
    """Prośba o powiadomienie: wariant, rodzaj, cena z chwili zapisu, status."""

    variant = WatchVariantSerializer(read_only=True)

    class Meta:
        model = Watch
        fields = [
            "id",
            "variant",
            "kind",
            "price_at_watch",
            "currency",
            "status",
            "created_at",
        ]
        read_only_fields = fields


class WatchWriteSerializer(serializers.Serializer):
    """Wejście do dodania obserwowania: wariant po SKU i rodzaj."""

    variant = serializers.SlugRelatedField(
        slug_field="sku",
        queryset=ProductVariant.objects.select_related("product"),
    )
    kind = serializers.ChoiceField(choices=WatchKind.choices)
