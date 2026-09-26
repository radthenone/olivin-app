from __future__ import annotations

from rest_framework import serializers

from apps.products.models import Product
from apps.reviews.models import COMMENT_MAX_LENGTH, Review
from apps.translations.serializers import TranslatedCharField


class ReviewSerializer(serializers.ModelSerializer):
    """Opinia publiczna: podpisana nazwą użytkownika i datą."""

    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Review
        fields = ["id", "username", "rating", "comment", "created_at"]
        read_only_fields = fields


class MyReviewSerializer(serializers.ModelSerializer):
    """Własna opinia klienta, ze statusem moderacji."""

    product = serializers.SlugRelatedField(slug_field="slug", read_only=True)

    class Meta:
        model = Review
        fields = [
            "id",
            "product",
            "rating",
            "comment",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class ProductToReviewSerializer(serializers.ModelSerializer):
    """Produkt z dostarczonego zamówienia, czekający na opinię klienta."""

    name = TranslatedCharField()

    class Meta:
        model = Product
        fields = ["id", "name", "slug"]
        read_only_fields = fields


class ReviewCreateSerializer(serializers.Serializer):
    """Wejście do złożenia opinii."""

    product = serializers.SlugRelatedField(
        slug_field="slug", queryset=Product.objects.published()
    )
    rating = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField(
        max_length=COMMENT_MAX_LENGTH, allow_blank=True, required=False, default=""
    )


class ReviewUpdateSerializer(serializers.Serializer):
    """Wejście do edycji opinii — zawsze wraca do moderacji."""

    rating = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField(
        max_length=COMMENT_MAX_LENGTH, allow_blank=True, required=False, default=""
    )
