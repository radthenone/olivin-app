from __future__ import annotations

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.orders.models import ENGRAVING_MAX_LENGTH, MAX_ITEM_QUANTITY, CartItem
from apps.products.models import (
    ImageStatus,
    ProductImage,
    ProductStatus,
    ProductVariant,
    RingSize,
)
from apps.promotions.models import CODE_MAX_LENGTH
from core.api.serializers import MoneySerializer

# Najwęższy rozmiar z `RENDITION_WIDTHS` — wiersz koszyka to miniatura,
# nie galeria.
THUMBNAIL_WIDTH = 400


def _first_ready_image(images) -> ProductImage | None:
    """Główne zdjęcie z gotowych; zdjęcie w przetwarzaniu nie wychodzi (ADR 0025)."""
    ready = [image for image in images if image.status == ImageStatus.READY]
    if not ready:
        return None
    return min(ready, key=lambda image: (not image.is_primary, image.position))


class CartVariantSerializer(serializers.ModelSerializer):
    """Tyle o wariancie, ile potrzebuje wiersz koszyka — nie cała karta produktu.

    Miniatura jest tu, a nie po stronie klienta: bez niej rozwijana lista
    koszyka musiałaby dociągać `GET /products/` po jednym żądaniu na wiersz,
    żeby pokazać, co klient właściwie kupuje.
    """

    product_name = serializers.CharField(source="product.name", read_only=True)
    product_slug = serializers.CharField(source="product.slug", read_only=True)
    is_made_to_order = serializers.BooleanField(
        source="product.is_made_to_order",
        read_only=True,
    )
    thumbnail_url = serializers.SerializerMethodField()

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
            "thumbnail_url",
        ]
        read_only_fields = fields

    @extend_schema_field(
        serializers.URLField(
            allow_null=True,
            help_text=(
                "Najwęższy gotowy rozmiar zdjęcia wariantu, a gdy wariant "
                "swojego nie ma — zdjęcia produktu. Pusty, gdy żadne zdjęcie "
                "nie jest jeszcze przetworzone."
            ),
        )
    )
    def get_thumbnail_url(self, obj: ProductVariant) -> str | None:
        from core.storage import PRODUCTS, object_url

        # Wybór w Pythonie na wstępnie pobranych zdjęciach, a nie zapytanie na
        # wiersz: `cart_items()` ściąga je raz dla całego koszyka. Kolejności
        # nie oddajemy bazie, bo puste `variant_id` układa się inaczej na
        # PostgreSQL i na SQLite — a testy chodzą na tym drugim.
        image = _first_ready_image(
            obj.images.all()  # type: ignore[missing-attribute]
        ) or _first_ready_image(obj.product.images.all())
        if image is None:
            return None
        key = (image.renditions or {}).get(str(THUMBNAIL_WIDTH))
        return object_url(PRODUCTS, key) if key else None


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

    Rabat to suma promocji na pozycjach. Kupon jest w odpowiedzi od
    początku, choć dziś zawsze zerowy: kontrakt ma nie zmieniać kształtu,
    gdy dojdą kupony.
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
        source="totals.item_count",
        read_only=True,
        help_text="Liczba pozycji, nie sztuk — para obrączek jest jedną pozycją",
    )
    subtotal = MoneySerializer(source="totals.subtotal", read_only=True)
    discount_amount = MoneySerializer(source="totals.discount_amount", read_only=True)
    coupon_amount = MoneySerializer(source="totals.coupon_amount", read_only=True)
    total = MoneySerializer(source="totals.total", read_only=True)
    promotion_code = serializers.CharField(
        read_only=True,
        allow_null=True,
        help_text="Kod promocji aktywowany w koszyku; pusty, gdy go nie ma",
    )


class PromotionCodeSerializer(serializers.Serializer):
    """Kod promocyjny wpisany w koszyku; wielkość liter nie ma znaczenia."""

    code = serializers.CharField(
        max_length=CODE_MAX_LENGTH, help_text="Kod promocji, np. LATO2026"
    )


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
