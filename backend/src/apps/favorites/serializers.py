from __future__ import annotations

from rest_framework import serializers

from apps.favorites.models import Favorite
from apps.products.models import Product
from apps.translations.serializers import TranslatedCharField


class FavoriteProductSerializer(serializers.ModelSerializer):
    """Produkt w kontekście listy ulubionych — tylko tyle, ile pokazuje karta."""

    name = TranslatedCharField()

    class Meta:
        model = Product
        fields = ["id", "name", "slug"]
        read_only_fields = fields


class FavoriteSerializer(serializers.ModelSerializer):
    """Wpis ulubionych: produkt i data dodania."""

    product = FavoriteProductSerializer(read_only=True)

    class Meta:
        model = Favorite
        fields = ["id", "product", "created_at"]
        read_only_fields = fields


class FavoriteWriteSerializer(serializers.Serializer):
    """Wejście do dodania produktu do ulubionych."""

    product = serializers.SlugRelatedField(
        slug_field="slug", queryset=Product.objects.published()
    )


class FavoriteMergeSerializer(serializers.Serializer):
    """Wejście do scalenia listy gościa: identyfikatory (slugi) produktów."""

    products = serializers.ListField(
        child=serializers.SlugField(), allow_empty=True, default=list
    )
