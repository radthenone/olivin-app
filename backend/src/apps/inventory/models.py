from __future__ import annotations

from datetime import timedelta

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Exists, F, IntegerField, OuterRef, Q, Subquery, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from common import TimestampedModel

# Próg, poniżej którego sklep pokazuje „ostatnie sztuki" (`CONTEXT.md`).
LOW_STOCK_THRESHOLD = 3

# Ile trwa rezerwacja stanu na czas płatności (`CONTEXT.md`, Reservation).
RESERVATION_TTL = timedelta(minutes=30)

# Nazwy adnotacji muszą się różnić od property `on_hand`, `reserved`
# i `available`: Django przypisuje adnotacje przez `setattr`, a property
# bez settera to wywraca.
ON_HAND = "on_hand_quantity"
RESERVED = "reserved_quantity"
AVAILABLE = "available_quantity"


def active_reservations_filter(prefix: str = "") -> Q:
    """Rezerwacje, które faktycznie trzymają stan — aktywne i nieprzeterminowane.

    Przeterminowana rezerwacja przestaje liczyć się od razu, a nie dopiero
    po przejściu zadania okresowego: spóźniony obchód nie może zamrażać
    towaru, którego nikt już nie kupuje.
    """
    return Q(**{f"{prefix}status": ReservationStatus.ACTIVE}) & Q(
        **{f"{prefix}expires_at__gt": timezone.now()}
    )


class ReservationStatus(models.TextChoices):
    ACTIVE = "active", "Aktywna"
    RELEASED = "released", "Zwolniona"
    CONSUMED = "consumed", "Rozliczona"


class StockMovementReason(models.TextChoices):
    """Przyczyna ruchu. Stan bez przyczyny jest nie do rozliczenia."""

    DELIVERY = "delivery", "Dostawa"
    SALE = "sale", "Sprzedaż"
    RETURN = "return", "Zwrot"
    CORRECTION = "correction", "Korekta inwentaryzacyjna"
    LOSS = "loss", "Ubytek"


def _movement_total(outer: str = "pk"):
    """Suma ruchów magazynowych jako podzapytanie."""
    return Subquery(
        StockMovement.objects.filter(item=OuterRef(outer))
        .values("item")
        .annotate(total=Sum("quantity"))
        .values("total"),
        output_field=IntegerField(),
    )


def _reservation_total(outer: str):
    """Suma aktywnych rezerwacji wariantu jako podzapytanie."""
    return Subquery(
        Reservation.objects.filter(
            active_reservations_filter(), variant=OuterRef(outer)
        )
        .values("variant")
        .annotate(total=Sum("quantity"))
        .values("total"),
        output_field=IntegerField(),
    )


class ReservationQuerySet(models.QuerySet["Reservation"]):
    def active(self) -> ReservationQuerySet:
        """Rezerwacje, które w tej chwili trzymają stan."""
        return self.filter(active_reservations_filter())

    def expired(self) -> ReservationQuerySet:
        """Aktywne, którym minął termin — do zwolnienia przez zadanie okresowe."""
        return self.filter(
            status=ReservationStatus.ACTIVE, expires_at__lte=timezone.now()
        )


class Reservation(TimestampedModel):
    """Czasowe wyłączenie ilości wariantu z dostępności (`CONTEXT.md`, Reservation).

    Trwa tyle, ile płatność — pół godziny od rozpoczęcia zapłaty. Wygasa
    sama: suma liczy wyłącznie rezerwacje nieprzeterminowane, więc stan
    wraca co do sekundy, a zadanie okresowe tylko sprząta status. Gdyby było
    odwrotnie, spóźniony obchód zamrażałby towar, którego nikt nie kupuje.

    Produkt na zamówienie rezerwacji nie ma w ogóle (ADR 0024): wyrób
    powstaje po złożeniu zamówienia, więc nie ma czego wyłączać z dostępności.
    """

    variant = models.ForeignKey(
        "products.ProductVariant",
        on_delete=models.PROTECT,
        related_name="reservations",
        help_text="Wariant, którego ilość jest wyłączona z dostępności",
    )
    quantity = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Liczba sztuk wyłączona z dostępności",
    )
    expires_at = models.DateTimeField(
        help_text="Chwila, po której rezerwacja przestaje trzymać stan",
    )
    status = models.CharField(
        max_length=16,
        choices=ReservationStatus.choices,
        default=ReservationStatus.ACTIVE,
        help_text="Aktywna trzyma stan; zwolniona i rozliczona już nie",
    )

    objects: ReservationQuerySet = ReservationQuerySet.as_manager()  # type: ignore[bad-assignment]

    class Meta:
        verbose_name = "Rezerwacja"
        verbose_name_plural = "Rezerwacje"
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["status", "expires_at"])]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity__gte=1),
                name="reservation_quantity_is_positive",
            )
        ]

    def __str__(self) -> str:
        return f"{self.variant.sku} × {self.quantity} ({self.get_status_display()})"  # type: ignore[missing-attribute]

    @property
    def is_active(self) -> bool:
        return (
            self.status == ReservationStatus.ACTIVE and self.expires_at > timezone.now()
        )


class InventoryItemQuerySet(models.QuerySet["InventoryItem"]):
    def with_stock(self) -> InventoryItemQuerySet:
        """Dokłada stan liczony z ruchów, rezerwacje i ilość faktycznie dostępną.

        Ani jedno, ani drugie nie jest kolumną: kolumna daje się nadpisać
        ręcznie i wtedy przestaje zgadzać się z historią, która ją tłumaczy
        (`CONTEXT.md`, StockMovement i Reservation).

        Obie sumy idą podzapytaniami, a nie dwoma `Sum` po złączeniach: dwa
        złączenia w jednym zapytaniu mnożą się przez siebie i stan wariantu
        z trzema rezerwacjami wyszedłby potrojony.
        """
        return self.annotate(
            **{
                ON_HAND: Coalesce(_movement_total(), 0),
                RESERVED: Coalesce(_reservation_total("variant_id"), 0),
            }
        ).annotate(**{AVAILABLE: F(ON_HAND) - F(RESERVED)})


class InventoryItem(TimestampedModel):
    """Stan magazynowy wariantu (`CONTEXT.md`, InventoryItem).

    Wariant bez stanu nie znika z katalogu — jest widoczny jako niedostępny.
    Produkt na zamówienie nie ma tego rekordu w ogóle (ADR 0024): nie ma czego
    liczyć, bo wyrób powstaje po złożeniu zamówienia.
    """

    variant = models.OneToOneField(
        "products.ProductVariant",
        on_delete=models.CASCADE,
        related_name="inventory",
    )
    objects: InventoryItemQuerySet = InventoryItemQuerySet.as_manager()  # type: ignore[bad-assignment]

    class Meta:
        verbose_name = "Stan magazynowy"
        verbose_name_plural = "Stany magazynowe"
        ordering = ["variant__sku"]

    def __str__(self) -> str:
        return f"{self.variant.sku}: {self.available} dostępnych"

    @property
    def on_hand(self) -> int:
        """Stan jako suma ruchów — nigdy pole nadpisywane."""
        total = self.movements.aggregate(total=Sum("quantity"))["total"]  # type: ignore[missing-attribute]
        return total or 0

    @property
    def reserved(self) -> int:
        """Ilość wyłączona z dostępności jako suma aktywnych rezerwacji.

        Nie kolumna: kolumna daje się nadpisać i wtedy przestaje zgadzać się
        z rezerwacjami, które ją uzasadniają — dokładnie ten sam powód, dla
        którego stan jest sumą ruchów, a nie liczbą wpisaną ręcznie.
        """
        total = Reservation.objects.filter(
            active_reservations_filter(),
            variant_id=self.variant_id,  # type: ignore[missing-attribute]
        ).aggregate(total=Sum("quantity"))["total"]
        return total or 0

    @property
    def available(self) -> int:
        return self.on_hand - self.reserved


class StockMovement(TimestampedModel):
    """Pojedyncza zmiana stanu wraz z przyczyną (`CONTEXT.md`, StockMovement).

    Ilość bywa ujemna — sprzedaż i ubytek zdejmują ze stanu. Stan wariantu
    jest sumą tych wierszy, więc ruch raz zapisany zostaje: korektę robi się
    kolejnym ruchem, a nie edycją poprzedniego.
    """

    item = models.ForeignKey(
        InventoryItem,
        on_delete=models.CASCADE,
        related_name="movements",
    )
    quantity = models.IntegerField(
        help_text="Zmiana stanu; ujemna zdejmuje ze stanu",
    )
    reason = models.CharField(
        max_length=16,
        choices=StockMovementReason.choices,
        help_text="Przyczyna ruchu",
    )
    note = models.CharField(
        max_length=200,
        blank=True,
        help_text="Uzupełnienie przyczyny, np. numer dostawy",
    )

    class Meta:
        verbose_name = "Ruch magazynowy"
        verbose_name_plural = "Ruchy magazynowe"
        ordering = ["-created_at", "-id"]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(quantity=0),
                name="stock_movement_quantity_is_not_zero",
            )
        ]

    def __str__(self) -> str:
        return f"{self.quantity:+d} ({self.get_reason_display()})"


def available_variants_subquery():
    """Warianty produktu, które klient może dziś kupić.

    Produkt na zamówienie jest dostępny zawsze — nie ma stanu, bo powstaje
    po złożeniu zamówienia (ADR 0024). Pozostałe muszą mieć dodatnią różnicę
    między sumą ruchów a ilością zarezerwowaną.
    """
    from apps.products.models import ProductVariant

    from apps.products.models import ProductVariant  # noqa: F811

    return (
        ProductVariant.objects.filter(product=OuterRef("pk"))
        .annotate(
            variant_on_hand=Coalesce(_movement_total("inventory__pk"), 0),
            variant_reserved=Coalesce(_reservation_total("pk"), 0),
        )
        .filter(
            Q(product__is_made_to_order=True)
            | Q(variant_on_hand__gt=F("variant_reserved"))
        )
    )


def has_available_variant():
    """Wyrażenie do adnotacji produktu: czy cokolwiek da się kupić."""
    return Exists(available_variants_subquery())
