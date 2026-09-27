from __future__ import annotations

from django.core.validators import MinValueValidator
from django.db import models

from common import TimestampedModel
from common.money import CurrencyField, Money, MoneyAmountField


class CostComponent(TimestampedModel):
    """Nazwana pozycja kosztu wykonania wariantu (`CONTEXT.md`, CostComponent).

    Robocizna, kamień, rodowanie, oprawa — lista otwarta, bez z góry ustalonych
    rodzajów. To rozbicie jest powodem, dla którego wzór ceny w ogóle działa
    dla wyrobów z kamieniami: kurs kruszcu opisuje tylko metal.
    """

    variant = models.ForeignKey(
        "products.ProductVariant",
        on_delete=models.CASCADE,
        related_name="cost_components",
    )
    name = models.CharField(
        max_length=80,
        help_text="Nazwa pozycji kosztu, np. robocizna, rodowanie, oprawa",
    )
    amount = MoneyAmountField(
        validators=[MinValueValidator(0)],
        help_text="Kwota w groszach",
    )
    currency = CurrencyField()

    class Meta:
        verbose_name = "Składnik kosztu"
        verbose_name_plural = "Składniki kosztu"
        ordering = ["name", "id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gte=0),
                name="cost_component_amount_is_not_negative",
            )
        ]

    def __str__(self) -> str:
        return f"{self.name}: {self.money}"

    @property
    def money(self) -> Money:
        return Money(self.amount, self.currency)
