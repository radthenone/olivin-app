from __future__ import annotations

from django.core.validators import MinValueValidator
from django.db import models

from common import TimestampedModel
from common.money import CurrencyField, Money, MoneyAmountField


class PaymentStatus(models.TextChoices):
    """Stan pojedynczej próby zapłaty (`CONTEXT.md`, Payment)."""

    PENDING = "pending", "Oczekuje na operatora"
    SUCCEEDED = "succeeded", "Zapłacona"
    FAILED = "failed", "Nieudana"
    REFUNDING = "refunding", "Zwrot w toku"
    REFUNDED = "refunded", "Zwrócona"
    REFUND_FAILED = "refund_failed", "Zwrot odrzucony"


class RefundReason(models.TextChoices):
    """Dlaczego sklep oddaje pieniądze — decyduje, co stanie się z zamówieniem.

    Zwrot wraca zdarzeniem od operatora, a wtedy trzeba wiedzieć, czy
    zamówienie ma zostać anulowane, czy to nadmiarowa wpłata na zamówienie,
    które już zapłacono albo zamknięto.
    """

    CANCELLATION = "cancellation", "Anulowanie przez klienta"
    OUT_OF_STOCK = "out_of_stock", "Towar zszedł przed rozliczeniem"
    ORDER_CLOSED = "order_closed", "Zamówienie nie czekało już na zapłatę"


class Payment(TimestampedModel):
    """Pojedyncza próba zapłaty za zamówienie (`CONTEXT.md`, Payment).

    Każda próba to osobny wiersz: nieudana zostaje jako ślad, a kolejna
    zakłada nową intencję u operatora. Kwota jest kopią kwoty zamówienia
    z chwili założenia intencji — to ją operator obciążył, nie bieżącą.
    """

    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.PROTECT,
        related_name="payments",
    )
    intent_id = models.CharField(
        max_length=255,
        unique=True,
        help_text="Identyfikator intencji płatniczej u operatora",
    )
    amount = MoneyAmountField(
        validators=[MinValueValidator(1)],
        help_text="Kwota intencji w groszach",
    )
    currency = CurrencyField()
    status = models.CharField(
        max_length=16,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )
    refund_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="Identyfikator zwrotu u operatora",
    )
    refund_reason = models.CharField(
        max_length=16,
        choices=RefundReason.choices,
        blank=True,
    )

    class Meta:
        verbose_name = "Płatność"
        verbose_name_plural = "Płatności"
        ordering = ["-created_at", "-id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name="payment_amount_is_positive",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.intent_id} ({self.get_status_display()})"  # type: ignore[missing-attribute]

    @property
    def amount_money(self) -> Money:
        return Money(self.amount, self.currency)


class WebhookEvent(TimestampedModel):
    """Zdarzenie od operatora zapisane po to, by nie przetworzyć go dwa razy.

    Operator dostarcza zdarzenie „co najmniej raz” (ADR 0012): unikalny
    identyfikator jest jedyną rzeczą, która odróżnia powtórkę od nowej
    zapłaty.
    """

    event_id = models.CharField(max_length=255, unique=True)
    kind = models.CharField(
        max_length=64,
        help_text="Rodzaj zdarzenia w nazewnictwie operatora",
    )
    payload = models.JSONField(default=dict)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Zdarzenie operatora"
        verbose_name_plural = "Zdarzenia operatora"
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return f"{self.event_id} ({self.kind})"
