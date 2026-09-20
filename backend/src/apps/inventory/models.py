from __future__ import annotations

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Exists, F, OuterRef, Q, Sum
from django.db.models.functions import Coalesce

from common import TimestampedModel

# Próg, poniżej którego sklep pokazuje „ostatnie sztuki" (`CONTEXT.md`).
LOW_STOCK_THRESHOLD = 3

# Nazwy adnotacji muszą się różnić od property `on_hand` i `available`:
# Django przypisuje adnotacje przez `setattr`, a property bez settera
# to wywraca.
ON_HAND = "on_hand_quantity"
AVAILABLE = "available_quantity"


class StockMovementReason(models.TextChoices):
    """Przyczyna ruchu. Stan bez przyczyny jest nie do rozliczenia."""

    DELIVERY = "delivery", "Dostawa"
    SALE = "sale", "Sprzedaż"
    RETURN = "return", "Zwrot"
    CORRECTION = "correction", "Korekta inwentaryzacyjna"
    LOSS = "loss", "Ubytek"


class InventoryItemQuerySet(models.QuerySet["InventoryItem"]):
    def with_stock(self) -> InventoryItemQuerySet:
        """Dokłada stan liczony z ruchów oraz ilość faktycznie dostępną.

        Stan nie jest kolumną, bo kolumna daje się nadpisać ręcznie i wtedy
        przestaje zgadzać się z historią ruchów (`CONTEXT.md`, StockMovement).
        """
        return self.annotate(
            **{
                ON_HAND: Coalesce(Sum("movements__quantity"), 0),
            }
        ).annotate(**{AVAILABLE: F(ON_HAND) - F("reserved")})


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
    reserved = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text=(
            "Ilość wyłączona z dostępności na czas płatności. Prowadzi ją "
            "zamówienie — `Reservation` nie należy do magazynu."
        ),
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

    return (
        ProductVariant.objects.filter(product=OuterRef("pk"))
        .annotate(
            variant_on_hand=Coalesce(Sum("inventory__movements__quantity"), 0),
            variant_reserved=Coalesce(F("inventory__reserved"), 0),
        )
        .filter(
            Q(product__is_made_to_order=True)
            | Q(variant_on_hand__gt=F("variant_reserved"))
        )
    )


def has_available_variant():
    """Wyrażenie do adnotacji produktu: czy cokolwiek da się kupić."""
    return Exists(available_variants_subquery())
