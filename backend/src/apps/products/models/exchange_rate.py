from __future__ import annotations

from decimal import ROUND_CEILING, Decimal

from django.db import models

from common import TimestampedModel
from common.money import DEFAULT_CURRENCY, CurrencyField, Money

EURO = "EUR"


class ExchangeRateQuerySet(models.QuerySet["ExchangeRate"]):
    def current(self, currency: str) -> ExchangeRate | None:
        """Najnowszy kurs waluty — obowiązuje od razu, bez aktywacji (ADR 0022)."""
        return (
            self.filter(currency=currency, base_currency=DEFAULT_CURRENCY)
            .order_by("-effective_on", "-created_at")
            .first()
        )


class ExchangeRate(TimestampedModel):
    """Kurs złotego do waluty obcej (`CONTEXT.md`, ExchangeRate).

    W przeciwieństwie do `MetalRate` nie ma cyklu życia: kurs waluty nie
    zmienia marży, tylko zapis tej samej ceny, więc najnowszy wpis działa
    od razu (ADR 0019, uzupełnienie 2026-09-22).
    """

    base_currency = CurrencyField(help_text="Waluta cen źródłowych")
    currency = CurrencyField(default=EURO, help_text="Waluta, na którą przeliczamy")
    rate = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        help_text="Ile jednostek waluty bazowej kosztuje jedna jednostka waluty",
    )
    effective_on = models.DateField(help_text="Dzień, z którego pochodzi notowanie")
    source = models.CharField(
        max_length=64,
        help_text="Skąd pochodzi kurs — jedyne miejsce, w którym pada nazwa dostawcy",
    )

    objects: ExchangeRateQuerySet = ExchangeRateQuerySet.as_manager()  # type: ignore[bad-assignment]

    class Meta:
        verbose_name = "Kurs waluty"
        verbose_name_plural = "Kursy walut"
        ordering = ["-effective_on", "-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["base_currency", "currency", "effective_on"],
                name="exchange_rate_single_per_pair_and_day",
            ),
            models.CheckConstraint(
                condition=models.Q(rate__gt=0),
                name="exchange_rate_is_positive",
            ),
        ]

    def __str__(self) -> str:
        return f"1 {self.currency} = {self.rate} {self.base_currency} ({self.effective_on})"

    def convert(self, amount: Money, rounding: str = ROUND_CEILING) -> Money:
        """Kwota w walucie bazowej przeliczona na walutę kursu.

        Domyślnie w górę do centa — przeliczenie nie może obniżyć ceny.
        Obie waluty mają dwie cyfry po przecinku, więc dzielimy wprost jednostki
        najmniejsze.
        """
        if amount.currency != self.base_currency:
            raise ValueError(
                f"cannot convert {amount.currency} with {self.base_currency} rate"
            )
        minor = (Decimal(amount.amount) / self.rate).quantize(
            Decimal(1), rounding=rounding
        )
        return Money(int(minor), self.currency)
