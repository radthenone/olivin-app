from __future__ import annotations

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from common import TimestampedModel
from common.money import CurrencyField, Money, MoneyAmountField


class ShippingZone(models.TextChoices):
    """Obszar dostawy. Stawka jest stała w obrębie strefy (ADR 0028)."""

    PL = "PL", "Polska"
    EU = "EU", "Unia Europejska"


class ShippingMethodKind(models.TextChoices):
    """Sposób dostarczenia — rozstrzyga, czego klient potrzebuje w kasie.

    Paczkomat wymaga kodu punktu odbioru, odbiór osobisty nie wymaga adresu
    ani przewoźnika, przesyłka do Unii chodzi inną stawką niż krajowa.
    """

    PARCEL_LOCKER = "parcel_locker", "Paczkomat"
    COURIER = "courier", "Kurier"
    PICKUP = "pickup", "Odbiór osobisty"
    EU = "eu", "Przesyłka do Unii"


class ShippingMethodQuerySet(models.QuerySet["ShippingMethod"]):
    def active(self) -> ShippingMethodQuerySet:
        return self.filter(is_active=True)

    def for_zone(self, zone: str) -> ShippingMethodQuerySet:
        return self.filter(zone=zone)

    def within_value_limit(self, order_value: Money) -> ShippingMethodQuerySet:
        """Metody, których górna wartość zamówienia nie została przekroczona.

        Metoda bez limitu (`max_order_value` puste) przechodzi zawsze —
        odbiór osobisty i kurier z deklaracją wartości nie mają górnej
        granicy odpowiedzialności, którą trzeba by respektować.
        """
        return self.filter(
            models.Q(max_order_value__isnull=True)
            | models.Q(max_order_value__gte=order_value.amount)
        )


class ShippingMethod(TimestampedModel):
    """Sposób dostawy ze stałą stawką dla strefy (`CONTEXT.md`, ShippingMethod).

    Ubezpieczenie jest wliczone w stawkę i klient go nie wybiera (ADR 0028);
    w modelu nie ma po nim śladu celowo — składka jest kosztem sklepu, a nie
    pozycją kasy. Górna wartość zamówienia odwzorowuje limit
    odpowiedzialności przewoźnika: powyżej niej metoda po prostu znika z listy.

    Mutacje wyłącznie przez panel (ADR 0021) — API tej listy tylko czyta.
    """

    name = models.CharField(
        max_length=120,
        help_text="Nazwa widoczna dla klienta, np. „Paczkomat InPost”",
    )
    kind = models.CharField(
        max_length=16,
        choices=ShippingMethodKind.choices,
        help_text="Sposób dostarczenia",
    )
    zone = models.CharField(
        max_length=2,
        choices=ShippingZone.choices,
        default=ShippingZone.PL,
        help_text="Strefa, dla której obowiązuje stawka",
    )
    rate = MoneyAmountField(
        validators=[MinValueValidator(0)],
        help_text="Stawka brutto w groszach; ubezpieczenie jest w niej zawarte",
    )
    currency = CurrencyField()
    max_order_value = MoneyAmountField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text=(
            "Górna wartość zamówienia w groszach, powyżej której metoda jest "
            "niedostępna. Puste oznacza brak limitu."
        ),
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Metoda wygaszona nie wychodzi przez API i nie da się jej wybrać",
    )

    objects: ShippingMethodQuerySet = ShippingMethodQuerySet.as_manager()  # type: ignore[bad-assignment]

    class Meta:
        verbose_name = "Metoda dostawy"
        verbose_name_plural = "Metody dostawy"
        ordering = ["zone", "rate", "name"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(rate__gte=0),
                name="shipping_method_rate_is_not_negative",
            ),
            models.CheckConstraint(
                condition=models.Q(max_order_value__isnull=True)
                | models.Q(max_order_value__gte=0),
                name="shipping_method_max_order_value_is_not_negative",
            ),
            # Odbiór osobisty nie jedzie przewoźnikiem, więc nie ma limitu
            # odpowiedzialności, który miałby go wyłączać. Reguła „odbiór
            # osobisty bez limitu” jest tu ograniczeniem w bazie, a nie
            # rozgałęzieniem w serwisie wyceny.
            models.CheckConstraint(
                condition=~models.Q(kind=ShippingMethodKind.PICKUP)
                | models.Q(max_order_value__isnull=True),
                name="shipping_method_pickup_has_no_value_limit",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.get_zone_display()})"  # type: ignore[missing-attribute]

    @property
    def rate_money(self) -> Money:
        return Money(self.rate, self.currency)

    @property
    def max_order_value_money(self) -> Money | None:
        if self.max_order_value is None:
            return None
        return Money(self.max_order_value, self.currency)

    def clean(self) -> None:
        super().clean()
        self._reject_pickup_with_value_limit()

    def save(self, *args, **kwargs) -> None:
        self._reject_pickup_with_value_limit()
        super().save(*args, **kwargs)

    def _reject_pickup_with_value_limit(self) -> None:
        if self.kind == ShippingMethodKind.PICKUP and self.max_order_value is not None:
            raise ValidationError(
                {
                    "max_order_value": (
                        "Odbiór osobisty nie ma górnej wartości zamówienia — "
                        "towar nie jedzie przewoźnikiem."
                    )
                }
            )
