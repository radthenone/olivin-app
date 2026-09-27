from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from apps.products.models.choices import Fineness, Material
from common import TimestampedModel
from common.money import CurrencyField, Money, MoneyAmountField


class MetalRateStatus(models.TextChoices):
    PROPOSED = "proposed", "Zaproponowany"
    ACTIVE = "active", "Aktywny"
    ARCHIVED = "archived", "Zarchiwizowany"


class MetalRateQuerySet(models.QuerySet["MetalRate"]):
    def active(self) -> MetalRateQuerySet:
        return self.filter(status=MetalRateStatus.ACTIVE)

    def active_for(self, metal: str, fineness: str) -> MetalRate | None:
        return self.active().filter(metal=metal, fineness=fineness).first()


class MetalRate(TimestampedModel):
    """Kurs kruszcu dla danej próby (`CONTEXT.md`, MetalRate).

    Ma cykl życia, bo kurs pobrany automatycznie nie może sam z siebie
    przecenić katalogu: zadanie okresowe wstawia go jako **zaproponowany**,
    właściciel **aktywuje** go w panelu i dopiero wtedy ceny się przeliczają
    (ADR 0022). Kurs niezatwierdzony niczego nie zmienia.
    """

    metal = models.CharField(
        max_length=16,
        choices=Material.choices,
        help_text="Kruszec, którego dotyczy kurs",
    )
    fineness = models.CharField(
        max_length=3,
        choices=Fineness.choices,
        help_text="Próba kruszcu — kurs za gram zależy od zawartości metalu",
    )
    price_per_gram = MoneyAmountField(
        validators=[MinValueValidator(1)],
        help_text="Cena za gram w groszach",
    )
    currency = CurrencyField()
    quoted_on = models.DateField(
        help_text="Dzień, z którego pochodzi notowanie",
    )
    source = models.CharField(
        max_length=64,
        help_text="Skąd pochodzi kurs — jedyne miejsce, w którym pada nazwa dostawcy",
    )
    status = models.CharField(
        max_length=16,
        choices=MetalRateStatus.choices,
        default=MetalRateStatus.PROPOSED,
        help_text="Tylko kurs aktywny wpływa na ceny wariantów",
    )
    activated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Chwila aktywacji; puste dopóki kurs nie został zatwierdzony",
    )
    activated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activated_metal_rates",
        help_text="Kto zatwierdził kurs — zostaje w dzienniku zmian",
    )

    objects: MetalRateQuerySet = MetalRateQuerySet.as_manager()  # type: ignore[bad-assignment]

    class Meta:
        verbose_name = "Kurs kruszcu"
        verbose_name_plural = "Kursy kruszców"
        ordering = ["-quoted_on", "-created_at", "-id"]
        constraints = [
            # Dwa aktywne kursy tego samego kruszcu i próby znaczyłyby, że
            # cena wariantu zależy od tego, który z nich baza zwróci pierwszy.
            models.UniqueConstraint(
                fields=["metal", "fineness"],
                condition=models.Q(status=MetalRateStatus.ACTIVE),
                name="metal_rate_single_active_per_metal_and_fineness",
            ),
            models.CheckConstraint(
                condition=models.Q(price_per_gram__gt=0),
                name="metal_rate_price_is_positive",
            ),
        ]
        indexes = [models.Index(fields=["metal", "fineness", "status"])]

    def __str__(self) -> str:
        return f"{self.get_metal_display()} {self.fineness} — {self.price} / g"

    @property
    def price(self) -> Money:
        return Money(self.price_per_gram, self.currency)

    @property
    def is_active(self) -> bool:
        return self.status == MetalRateStatus.ACTIVE

    def clean(self) -> None:
        super().clean()
        if self.status == MetalRateStatus.ACTIVE and self.activated_at is None:
            raise ValidationError(
                {
                    "status": (
                        "Kurs aktywuje się akcją w panelu, a nie zmianą pola — "
                        "inaczej ceny wariantów nie zostałyby przeliczone."
                    )
                }
            )
