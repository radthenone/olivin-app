from __future__ import annotations

from django_countries.serializer_fields import CountryField
from rest_framework import serializers

from apps.orders.models import Order, OrderItem, SalesDocument
from apps.orders.services import ShippingAddress
from apps.shipping.models import ShippingMethod
from core.api.serializers import MoneySerializer


class OrderItemSerializer(serializers.ModelSerializer):
    """Pozycja zamówienia — wyłącznie kopie z chwili złożenia (ADR 0010).

    Nie ma tu odwołania do dzisiejszej ceny wariantu ani do jego stanu:
    zamówienie ma pokazywać to, co klient kupił, a nie to, co jest w sklepie
    teraz.
    """

    unit_price = MoneySerializer(source="unit_price_money", read_only=True)
    goods_price = MoneySerializer(read_only=True)
    engraving_total = MoneySerializer(read_only=True)
    line_total = MoneySerializer(read_only=True)
    discount_amount = MoneySerializer(source="discount_money", read_only=True)
    discounted_total = MoneySerializer(read_only=True)
    is_pair = serializers.BooleanField(read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "variant",
            "product_name",
            "sku",
            "quantity",
            "size",
            "second_size",
            "engraving_text",
            "second_engraving_text",
            "is_pair",
            "is_made_to_order",
            "unit_price",
            "goods_price",
            "engraving_total",
            "line_total",
            "discount_amount",
            "discounted_total",
        ]
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    """Zamówienie w postaci, w jakiej ogląda je klient.

    Kwoty wychodzą policzone: klient nie składa sumy z pozycji, bo to
    backend rozstrzyga, ile jest do zapłaty (ADR 0012).
    """

    items = OrderItemSerializer(many=True, read_only=True)
    goods_total = MoneySerializer(read_only=True)
    shipping_cost = MoneySerializer(source="shipping_cost_money", read_only=True)
    discount_amount = MoneySerializer(source="discount_money", read_only=True)
    coupon_amount = MoneySerializer(source="coupon_money", read_only=True)
    total = MoneySerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "number",
            "status",
            "email",
            "recipient_name",
            "street",
            "street2",
            "city",
            "postal_code",
            "country",
            "shipping_method_name",
            "currency",
            "exchange_rate",
            "terms_version",
            "invoice_requested",
            "items",
            "goods_total",
            "shipping_cost",
            "discount_amount",
            "coupon_amount",
            "total",
            "created_at",
        ]
        read_only_fields = fields


class OrderCreateSerializer(serializers.Serializer):
    """Złożenie zamówienia: adres, metoda dostawy i — dla gościa — e-mail.

    Pozycji tu nie ma: biorą się z koszyka, który klient już zbudował
    (ADR 0030). Przysłanie ich w żądaniu pozwalałoby zamówić coś innego niż
    to, co klient widział w koszyku.
    """

    email = serializers.EmailField(
        required=False,
        allow_blank=True,
        default="",
        help_text="Adres gościa; pomijany przy zalogowanym kliencie",
    )
    recipient_name = serializers.CharField(max_length=200)
    street = serializers.CharField(max_length=255)
    street2 = serializers.CharField(
        max_length=255, required=False, allow_blank=True, default=""
    )
    city = serializers.CharField(max_length=100)
    postal_code = serializers.CharField(max_length=20)
    country = CountryField(
        help_text="Kod kraju ISO 3166-1 alfa-2; sklep wysyła do Polski i Unii",
    )
    shipping_method = serializers.PrimaryKeyRelatedField(
        queryset=ShippingMethod.objects.active(),
        help_text="Metoda dostawy wybrana w trzecim kroku kasy",
    )
    invoice_requested = serializers.BooleanField(
        required=False,
        default=False,
        help_text=(
            "Faktura imienna na odbiorcę i adres z zamówienia; potwierdzenie "
            "zamówienia powstaje zawsze"
        ),
    )

    def to_address(self) -> ShippingAddress:
        """Adres ze zwalidowanych danych jako typ domeny; kraj jako kod ISO."""
        data = self.validated_data
        return ShippingAddress(
            recipient_name=data["recipient_name"],
            street=data["street"],
            street2=data["street2"],
            city=data["city"],
            postal_code=data["postal_code"],
            country=str(data["country"]),
        )


class OrderLookupSerializer(serializers.Serializer):
    """Parametry, którymi gość dostaje się do swojego zamówienia.

    Sam numer nie wystarcza: adres e-mail jest drugim składnikiem, żeby numer
    podejrzany w cudzej wiadomości nie otwierał zamówienia.
    """

    email = serializers.EmailField(
        help_text="Adres podany przy składaniu zamówienia",
    )


class SalesDocumentSerializer(serializers.ModelSerializer):
    """Dokument sprzedaży do pobrania adresem podpisanym na czas (ADR 0025).

    Adres wygasa po `S3_SIGNED_URL_TTL` — klient pobiera listę na nowo,
    zamiast zapamiętywać odnośnik.
    """

    reference = serializers.CharField(read_only=True)
    url = serializers.SerializerMethodField(
        help_text="Adres PDF podpisany na czas; po wygaśnięciu pobierz listę ponownie",
    )

    class Meta:
        model = SalesDocument
        fields = ["id", "kind", "reference", "number", "year", "issued_on", "url"]
        read_only_fields = fields

    def get_url(self, obj: SalesDocument) -> str:
        from core.storage import DOCUMENTS, object_url

        return object_url(DOCUMENTS, obj.object_key)
