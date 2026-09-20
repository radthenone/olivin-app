from __future__ import annotations

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.products.models import Gemstone, Product, ProductImage, ProductVariant
from core.api.serializers import MoneySerializer


class ProductImageSerializer(serializers.ModelSerializer):
    """Zdjęcie z adresami wszystkich rozmiarów.

    Model trzyma same klucze (ADR 0025), więc adresy powstają tutaj — host
    i bucket zmieniają się razem ze środowiskiem.
    """

    urls = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ["id", "position", "is_primary", "alt_text", "urls"]
        read_only_fields = fields

    @extend_schema_field(
        serializers.DictField(
            child=serializers.URLField(),
            help_text="Adres zdjęcia dla każdej szerokości w pikselach",
        )
    )
    def get_urls(self, obj: ProductImage) -> dict[str, str]:
        from core.storage import PRODUCTS, object_url

        return {
            width: object_url(PRODUCTS, key)
            for width, key in (obj.renditions or {}).items()
        }


class GemstoneSerializer(serializers.ModelSerializer):
    """Kamień z parametrami i adresem certyfikatu, jeśli jest.

    Adres jest podpisany na czas, bo certyfikat leży w prywatnym buckecie
    `documents` (ADR 0025). Stały odnośnik do dokumentu laboratorium byłby
    dostępny dla każdego, kto go raz zobaczył.
    """

    certificate_url = serializers.SerializerMethodField()

    class Meta:
        model = Gemstone
        fields = [
            "id",
            "kind",
            "carat",
            "clarity",
            "colour",
            "cut",
            "laboratory",
            "certificate_number",
            "certificate_url",
        ]
        read_only_fields = fields

    @extend_schema_field(
        serializers.URLField(
            allow_null=True,
            help_text=(
                "Adres certyfikatu podpisany na czas; pusty, gdy kamień "
                "nie ma certyfikatu."
            ),
        )
    )
    def get_certificate_url(self, obj: Gemstone) -> str | None:
        if not obj.has_certificate:
            return None
        from core.storage import DOCUMENTS, object_url

        return object_url(DOCUMENTS, obj.certificate_key)


class ProductVariantSerializer(serializers.ModelSerializer):
    """Wariant widziany przez klienta.

    Cena jest tą, którą klient faktycznie zapłaci: ręczna ma pierwszeństwo
    przed wyliczoną (ADR 0022). Klient nie musi wiedzieć, która to która.
    """

    price = MoneySerializer(source="effective_price", read_only=True)
    available = serializers.IntegerField(
        read_only=True,
        allow_null=True,
        help_text=(
            "Liczba sztuk do kupienia; pusta dla produktu na zamówienie, "
            "który nie ma stanu magazynowego."
        ),
    )
    is_available = serializers.BooleanField(read_only=True)
    is_low_stock = serializers.BooleanField(
        read_only=True,
        help_text="Ostatnie sztuki — stan dodatni, ale nie większy niż trzy.",
    )
    images = serializers.SerializerMethodField()
    gemstones = GemstoneSerializer(many=True, read_only=True)

    class Meta:
        model = ProductVariant
        fields = [
            "id",
            "sku",
            "available",
            "is_available",
            "is_low_stock",
            "metal_color",
            "size",
            "length",
            "stone",
            "metal_weight_grams",
            "price",
            "vat_rate",
            "is_vat_exempt",
            "vat_exemption_basis",
            "images",
            "gemstones",
        ]
        read_only_fields = fields

    @extend_schema_field(ProductImageSerializer(many=True))
    def get_images(self, obj: ProductVariant) -> list[dict]:
        """Zdjęcia różnicujące wygląd tego wariantu; szkice pominięte."""
        ready = [
            image
            for image in obj.images.all()  # type: ignore[missing-attribute]
            if image.status == "ready"
        ]
        return list(ProductImageSerializer(ready, many=True, context=self.context).data)


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
    images = serializers.SerializerMethodField()

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
            "images",
            "variants",
        ]
        read_only_fields = fields

    @extend_schema_field(ProductImageSerializer(many=True))
    def get_images(self, obj: Product) -> list[dict]:
        """Galeria produktu. Zdjęcia w przetwarzaniu są pomijane — pół
        galerii jest gorsze niż galeria o jedno zdjęcie krótsza."""
        ready = [
            image
            for image in obj.images.all()  # type: ignore[missing-attribute]
            if image.status == "ready"
        ]
        return list(ProductImageSerializer(ready, many=True, context=self.context).data)
