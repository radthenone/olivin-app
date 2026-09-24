from __future__ import annotations

import secrets
from datetime import datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.functions import Lower

from apps.orders.models.cart import ENGRAVING_MAX_LENGTH, MAX_ITEM_QUANTITY
from apps.products.models.choices import RingSize
from common import TimestampedModel
from common.money import CurrencyField, Money, MoneyAmountField

if TYPE_CHECKING:
    from apps.accounts.models import Customer

# Zamówienie bez zapłaty przez dobę anuluje się samo (`CONTEXT.md`, Order).
UNPAID_ORDER_TTL = timedelta(hours=24)

# Gość bez konta nie złoży zamówienia droższego niż 10 000 zł (`.ai/project.md`).
GUEST_ORDER_LIMIT = 1_000_000

# Znaki numeru zamówienia: bez zer, jedynek, „I" i „O", żeby nikt nie mylił
# ich przy przepisywaniu numeru z wiadomości.
_NUMBER_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
_NUMBER_LENGTH = 10


class OrderStatus(models.TextChoices):
    """Etap cyklu życia zamówienia (`CONTEXT.md`, Order status)."""

    PENDING = "pending", "Oczekuje na zapłatę"
    PAID = "paid", "Opłacone"
    IN_PRODUCTION = "in_production", "W produkcji"
    PACKED = "packed", "Spakowane"
    SHIPPED = "shipped", "Wysłane"
    DELIVERED = "delivered", "Dostarczone"
    CANCELLED = "cancelled", "Anulowane"
    RETURNED = "returned", "Zwrócone"


# Przejścia są jednokierunkowe poza anulowaniem (`CONTEXT.md`, Order status).
# Mapa jest jawna, a nie liczona z kolejności: „pominięcie" etapu bywa
# poprawne (zamówienie bez produktu na zamówienie nie wchodzi w produkcję),
# a lista następników mówi to wprost.
ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    OrderStatus.PENDING: frozenset({OrderStatus.PAID, OrderStatus.CANCELLED}),
    OrderStatus.PAID: frozenset(
        {OrderStatus.IN_PRODUCTION, OrderStatus.PACKED, OrderStatus.CANCELLED}
    ),
    OrderStatus.IN_PRODUCTION: frozenset({OrderStatus.PACKED, OrderStatus.CANCELLED}),
    OrderStatus.PACKED: frozenset({OrderStatus.SHIPPED, OrderStatus.CANCELLED}),
    OrderStatus.SHIPPED: frozenset({OrderStatus.DELIVERED}),
    OrderStatus.DELIVERED: frozenset({OrderStatus.RETURNED}),
    OrderStatus.CANCELLED: frozenset(),
    OrderStatus.RETURNED: frozenset(),
}


def new_order_number() -> str:
    """Numer zamówienia: losowy, nie kolejny.

    Gość dostaje się do zamówienia adresem e-mail **i** numerem, więc numer
    kolejny pozwalałby zgadywać sąsiednie zamówienia i sprawdzać, czy dany
    adres coś kupił. Numeracja ciągła jest wymagana od dokumentu sprzedaży
    (ADR 0026), nie od zamówienia.
    """
    return "".join(secrets.choice(_NUMBER_ALPHABET) for _ in range(_NUMBER_LENGTH))


class OrderQuerySet(models.QuerySet["Order"]):
    def for_subject(
        self, *, user: Customer = None, email: str | None = None
    ) -> OrderQuerySet:
        """Zamówienia klienta albo gościa po e-mailu — nigdy obu naraz.

        Ścieżka gościa obejmuje wyłącznie zamówienia bez konta. Inaczej sam
        adres plus numer otwierałby — i pozwalał anulować — zamówienie
        zalogowanego klienta, mimo że to jego konto nim zarządza.
        """
        if user is not None:
            return self.filter(user=user)
        if email:
            return self.filter(user__isnull=True, email__iexact=email)
        return self.none()

    def unpaid_since(self, moment: datetime) -> OrderQuerySet:
        return self.filter(status=OrderStatus.PENDING, created_at__lt=moment)


class Order(TimestampedModel):
    """Zamówienie złożone przez klienta (`CONTEXT.md`, Order).

    Niemutowalne co do treści: adres, koszt dostawy, ceny i kurs waluty są
    kopiami z chwili złożenia (ADR 0010, 0019). Zmienia się wyłącznie status.
    Zamówienie powstaje **przed** zapłatą, w statusie `pending` — operator
    zwraca zdarzenie z identyfikatorem intencji, więc musi być z czym je
    powiązać (ADR 0030).
    """

    number = models.CharField(
        max_length=16,
        unique=True,
        default=new_order_number,
        editable=False,
        help_text="Numer, którym klient posługuje się w kontakcie ze sklepem",
    )
    user = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        help_text="Zalogowany klient; pusty przy zamówieniu gościa",
    )
    email = models.EmailField(
        help_text=(
            "Adres, pod który idzie potwierdzenie. Zawsze wypełniony — także "
            "dla klienta z kontem, bo zamówienie ma zostać czytelne po "
            "anonimizacji konta."
        ),
    )
    status = models.CharField(
        max_length=16,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
        help_text="Etap cyklu życia zamówienia",
    )

    # --- Kopia adresu dostawy ---------------------------------------------
    recipient_name = models.CharField(
        max_length=200,
        help_text="Imię i nazwisko odbiorcy z chwili złożenia zamówienia",
    )
    street = models.CharField(max_length=255)
    street2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(
        max_length=2,
        help_text="Kod kraju ISO 3166-1 alfa-2 z chwili złożenia zamówienia",
    )

    # --- Kopia metody dostawy ---------------------------------------------
    shipping_method = models.ForeignKey(
        "shipping.ShippingMethod",
        on_delete=models.PROTECT,
        related_name="orders",
        help_text="Wybrana metoda dostawy; kwota i nazwa są skopiowane obok",
    )
    shipping_method_name = models.CharField(
        max_length=120,
        help_text="Nazwa metody z chwili złożenia — cennik wolno potem zmienić",
    )
    shipping_cost = MoneyAmountField(
        validators=[MinValueValidator(0)],
        help_text="Koszt dostawy w groszach, zamrożony przy składaniu zamówienia",
    )

    # --- Pieniądze ---------------------------------------------------------
    currency = CurrencyField()
    exchange_rate = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        default=Decimal("1.000000"),
        help_text=(
            "Kurs, po którym przeliczono ceny źródłowe na walutę zamówienia. "
            "Jeden przy sprzedaży w złotych (ADR 0019)."
        ),
    )
    discount_amount = MoneyAmountField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Suma rabatów z promocji; wypełni ją bilet promocji",
    )
    coupon_amount = MoneyAmountField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Kwota pokryta kuponem; wypełni ją bilet kuponów",
    )

    # --- Dokumenty ---------------------------------------------------------
    invoice_requested = models.BooleanField(
        default=False,
        help_text=(
            "Klient poprosił o fakturę imienną — wystawiana na odbiorcę "
            "i adres z zamówienia (ADR 0026)"
        ),
    )

    # --- Zgoda -------------------------------------------------------------
    terms_document = models.ForeignKey(
        "consents.ConsentDocument",
        on_delete=models.PROTECT,
        related_name="orders",
        help_text="Wersja regulaminu zaakceptowana przy składaniu zamówienia",
    )
    terms_version = models.CharField(
        max_length=32,
        editable=False,
        help_text="Kopia oznaczenia wersji regulaminu z chwili złożenia",
    )

    objects: OrderQuerySet = OrderQuerySet.as_manager()  # type: ignore[bad-assignment]

    class Meta:
        verbose_name = "Zamówienie"
        verbose_name_plural = "Zamówienia"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(Lower("email"), name="order_email_lower_idx"),
            models.Index(fields=["status", "created_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(shipping_cost__gte=0),
                name="order_shipping_cost_is_not_negative",
            ),
            models.CheckConstraint(
                condition=models.Q(discount_amount__gte=0)
                & models.Q(coupon_amount__gte=0),
                name="order_reductions_are_not_negative",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.number} ({self.get_status_display()})"  # type: ignore[missing-attribute]

    @property
    def is_guest(self) -> bool:
        return self.user_id is None  # type: ignore[missing-attribute]

    @property
    def has_made_to_order_item(self) -> bool:
        """Czy cokolwiek w zamówieniu powstaje dopiero po jego złożeniu (ADR 0024)."""
        return any(item.is_made_to_order for item in self.items.all())  # type: ignore[missing-attribute]

    @property
    def goods_total(self) -> Money:
        """Wartość towaru wraz z grawerunkiem, przed rabatami i dostawą."""
        zero = Money.zero(self.currency)
        return sum((item.line_total for item in self.items.all()), start=zero)  # type: ignore[missing-attribute]

    @property
    def shipping_cost_money(self) -> Money:
        return Money(self.shipping_cost, self.currency)

    @property
    def discount_money(self) -> Money:
        return Money(self.discount_amount, self.currency)

    @property
    def coupon_money(self) -> Money:
        return Money(self.coupon_amount, self.currency)

    @property
    def total(self) -> Money:
        """Kwota do zapłaty: towar po rabatach i kuponie plus dostawa.

        Kupon pokrywa wyłącznie towar (ADR 0011), więc odejmuje się przed
        doliczeniem dostawy, a nie po.
        """
        goods = self.goods_total - self.discount_money - self.coupon_money
        floor = Money.zero(self.currency)
        if goods < floor:
            goods = floor
        return goods + self.shipping_cost_money

    def can_transition_to(self, status: str) -> bool:
        if status not in ALLOWED_TRANSITIONS.get(self.status, frozenset()):
            return False
        if status == OrderStatus.IN_PRODUCTION:
            return self.has_made_to_order_item
        return True

    def transition_to(self, status: str) -> None:
        """Zmienia status, odrzucając przejście, którego cykl życia nie przewiduje.

        Etap `in_production` jest dostępny wyłącznie dla zamówienia z wyrobem
        na zamówienie — przy wyrobie z magazynu nie ma czego produkować
        (ADR 0024).
        """
        if not self.can_transition_to(status):
            raise ValidationError(
                {
                    "status": (
                        f"Ze statusu „{self.get_status_display()}” nie da się "  # type: ignore[missing-attribute]
                        f"przejść do „{OrderStatus(status).label}”."
                    )
                }
            )
        self.status = status
        self.save(update_fields=["status", "updated_at"])

    def save(self, *args, **kwargs) -> None:
        if not self.terms_version and self.terms_document_id is not None:  # type: ignore[missing-attribute]
            self.terms_version = self.terms_document.version
        super().save(*args, **kwargs)


class OrderItem(TimestampedModel):
    """Pozycja zamówienia z kopią danych wariantu (`CONTEXT.md`, OrderItem).

    Kopia, a nie odwołanie przez klucz obcy (ADR 0010): bez niej historia
    zamówień, faktury i zwroty zaczynają kłamać po każdej zmianie cennika —
    co w biżuterii, gdzie ceny chodzą za kursem kruszcu, zdarza się co
    miesiąc. Klucz obcy do wariantu zostaje, ale wyłącznie po to, żeby
    dało się dojść do karty produktu; wycena go nie czyta.
    """

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )
    variant = models.ForeignKey(
        "products.ProductVariant",
        on_delete=models.PROTECT,
        related_name="order_items",
        help_text="Kupiony wariant — do odnalezienia karty produktu, nie do wyceny",
    )

    # --- Kopia opisu -------------------------------------------------------
    product_name = models.CharField(max_length=200)
    sku = models.CharField(max_length=64)
    is_made_to_order = models.BooleanField(
        help_text="Czy wyrób powstaje dopiero po złożeniu zamówienia (ADR 0024)",
    )

    # --- Kopia ceny i podatku ---------------------------------------------
    quantity = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
        help_text=f"Liczba sztuk pozycji, najwyżej {MAX_ITEM_QUANTITY}",
    )
    unit_price = MoneyAmountField(
        validators=[MinValueValidator(0)],
        help_text="Cena brutto jednego egzemplarza z chwili złożenia zamówienia",
    )
    vat_rate = models.DecimalField(
        max_digits=4,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Stawka podatku jako ułamek; pusta wyłącznie przy zwolnieniu",
    )
    is_vat_exempt = models.BooleanField(default=False)
    vat_exemption_basis = models.CharField(max_length=200, blank=True)

    # --- Kopia personalizacji ---------------------------------------------
    engraving_text = models.CharField(max_length=ENGRAVING_MAX_LENGTH, blank=True)
    engraving_price = MoneyAmountField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Cena grawerunku jednego egzemplarza z chwili złożenia",
    )
    size = models.CharField(
        max_length=2,
        blank=True,
        help_text="Rozmiar pierwszego egzemplarza, skopiowany z wariantu",
    )
    second_size = models.CharField(
        max_length=2,
        choices=RingSize.choices,
        blank=True,
        help_text="Rozmiar drugiego egzemplarza pary (ADR 0024)",
    )
    second_engraving_text = models.CharField(
        max_length=ENGRAVING_MAX_LENGTH, blank=True
    )

    discount_amount = MoneyAmountField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Rabat naliczony na tę pozycję; wypełni go bilet promocji",
    )

    class Meta:
        verbose_name = "Pozycja zamówienia"
        verbose_name_plural = "Pozycje zamówienia"
        ordering = ["created_at", "id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity__gte=1),
                name="order_item_quantity_is_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(unit_price__gte=0)
                & models.Q(engraving_price__gte=0)
                & models.Q(discount_amount__gte=0),
                name="order_item_amounts_are_not_negative",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.sku} × {self.quantity}"

    @property
    def currency(self) -> str:
        return self.order.currency

    @property
    def is_pair(self) -> bool:
        return bool(self.second_size)

    @property
    def specimen_count(self) -> int:
        return 2 if self.is_pair else 1

    @property
    def unit_price_money(self) -> Money:
        return Money(self.unit_price, self.currency)

    @property
    def goods_price(self) -> Money:
        return self.unit_price_money * (self.specimen_count * self.quantity)

    @property
    def engraving_total(self) -> Money:
        if not self.engraving_text:
            return Money.zero(self.currency)
        return Money(self.engraving_price, self.currency) * (
            self.specimen_count * self.quantity
        )

    @property
    def line_total(self) -> Money:
        return self.goods_price + self.engraving_total
