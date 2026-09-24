from __future__ import annotations

from rest_framework import serializers

from apps.promotions.models import Promotion
from core.api.serializers import MoneySerializer


class PromotionSerializer(serializers.ModelSerializer):
    """Promocja widoczna w sklepie — bez kodu i bez limitów.

    Limity są sprawą sklepu: klient dowie się o wyczerpaniu z wyceny
    koszyka, a pokazywanie liczników zachęcałoby do wyścigu o ostatnie użycia.
    """

    min_cart_value = MoneySerializer(
        source="min_cart_money",
        read_only=True,
        allow_null=True,
        help_text="Minimalna wartość koszyka przed rabatami; pusta — bez progu",
    )

    class Meta:
        model = Promotion
        fields = [
            "id",
            "name",
            "kind",
            "value",
            "currency",
            "whole_catalog",
            "products",
            "collections",
            "categories",
            "starts_at",
            "ends_at",
            "min_cart_value",
            "requires_premium",
        ]
        read_only_fields = fields
