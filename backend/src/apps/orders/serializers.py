from __future__ import annotations

from rest_framework import serializers

from apps.orders.models import ENGRAVING_MAX_LENGTH, MAX_ITEM_QUANTITY, CartItem
from apps.products.models import ProductStatus, ProductVariant, RingSize
from core.api.serializers import MoneySerializer


class CartVariantSerializer(serializers.ModelSerializer):
    """Tyle o wariancie, ile potrzebuje wiersz koszyka — nie cała karta produktu."""

    product_name = serializers.CharField(source="product.name", read_only=True)
    product_slug = serializers.CharField(source="product.slug", read_only=True)
    is_made_to_order = serializers.BooleanField(
        source="product.is_made_to_order",
        read_only=True,
    )

    class Meta:
        model = ProductVariant
        fields = [
            "id",
            "sku",
            "product_name",
            "product_slug",
            "metal_color",
            "size",
            "length",
            "is_made_to_order",
        ]
        read_only_fields = fields


class CartItemSerializer(serializers.ModelSerializer):
    """Pozycja koszyka z wyceną liczoną przy odczycie, nie zamrożoną.

    Cena idzie prosto z wariantu, bo koszyk ma pokazywać dzisiejszy cennik
    (`CONTEXT.md`, CartItem). Kopia powstaje dopiero w pozycji zamówienia
    (ADR 0010).
    """

    variant = CartVariantSerializer(read_only=True)
    unit_price = MoneySerializer(read_only=True)
    goods_price = MoneySerializer(read_only=True)
    engraving_price = MoneySerializer(read_only=True)
    line_total = MoneySerializer(read_only=True)
    is_pair = serializers.BooleanField(read_only=True)

    class Meta:
        model = CartItem
        fields = [
            "id",
            "variant",
            "quantity",
            "engraving_text",
            "second_size",
            "second_engraving_text",
            "is_pair",
            "unit_price",
            "goods_price",
            "engraving_price",
            "line_total",
        ]
        read_only_fields = fields


class CartSerializer(serializers.Serializer):
    """Pełny widok koszyka — krok pierwszy kasy (ADR 0030).

    Rabat i kupon są w odpowiedzi od początku, choć dziś zawsze zerowe:
    kontrakt ma nie zmieniać kształtu, gdy dojdą promocje i kupony.
    """

    cart_token = serializers.CharField(
        read_only=True,
        allow_null=True,
        help_text=(
            "Token koszyka gościa do odesłania nagłówkiem `X-Cart-Token`; "
            "pusty przy koszyku zalogowanego klienta"
        ),
    )
    items = CartItemSerializer(many=True, read_only=True)
    item_count = serializers.IntegerField(
        read_only=True,
        help_text="Liczba pozycji, nie sztuk — para obrączek jest jedną pozycją",
    )
    subtotal = MoneySerializer(read_only=True)
    discount_amount = MoneySerializer(read_only=True)
    coupon_amount = MoneySerializer(read_only=True)
    total = MoneySerializer(read_only=True)


class CartItemWriteSerializer(serializers.Serializer):
    """Dodanie pozycji do koszyka.

    Wariant wskazuje się identyfikatorem i musi pochodzić z opublikowanego
    produktu: szkic nie istnieje dla sklepu pod żadnym adresem, więc nie może
    wejść do koszyka bocznymi drzwiami.
    """

    variant = serializers.PrimaryKeyRelatedField(
        queryset=ProductVariant.objects.filter(
            product__status=ProductStatus.PUBLISHED
        ).select_related("product", "inventory"),
        help_text="Identyfikator kupowanego wariantu",
    )
    quantity = serializers.IntegerField(
        min_value=1,
        max_value=MAX_ITEM_QUANTITY,
        default=1,
        help_text=f"Liczba sztuk pozycji, najwyżej {MAX_ITEM_QUANTITY}",
    )
    engraving_text = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        max_length=ENGRAVING_MAX_LENGTH,
        help_text="Treść grawerunku; wymaga produktu grawerowalnego",
    )
    second_size = serializers.ChoiceField(
        choices=RingSize.choices,
        required=False,
        allow_blank=True,
        default="",
        help_text="Rozmiar drugiego egzemplarza pary (wyrób na zamówienie)",
    )
    second_engraving_text = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        max_length=ENGRAVING_MAX_LENGTH,
        help_text="Grawerunek drugiego egzemplarza, gdy ma być inny",
    )


class CartItemQuantitySerializer(serializers.Serializer):
    """Zmiana liczby sztuk pozycji; zero usuwa ją z koszyka."""

    quantity = serializers.IntegerField(
        min_value=0,
        max_value=MAX_ITEM_QUANTITY,
        help_text=f"Nowa liczba sztuk, najwyżej {MAX_ITEM_QUANTITY}; 0 usuwa pozycję",
    )
