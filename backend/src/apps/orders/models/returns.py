from __future__ import annotations

from datetime import timedelta

from django.core.validators import MinValueValidator
from django.db import models

from common import TimestampedModel
from common.money import Money, MoneyAmountField


class ReturnReason(models.TextChoices):
    """Podstawa zwrotu (`CONTEXT.md`, ReturnReason) — rozstrzyga o terminie."""

    WITHDRAWAL = "withdrawal", "Odstąpienie od umowy"
    COMPLAINT = "complaint", "Reklamacja"
    GOODWILL = "goodwill", "Zwrot dobrowolny"


# Terminy liczone od `Order.delivered_at`. Reklamacja to dwa lata
# kalendarzowe, nie 730 dni — patrz `services.returns.return_deadline`.
RETURN_PERIODS: dict[str, timedelta] = {
    ReturnReason.WITHDRAWAL: timedelta(days=14),
    ReturnReason.GOODWILL: timedelta(days=30),
}
COMPLAINT_YEARS = 2


class ClaimRequest(models.TextChoices):
    """Żądanie klienta przy reklamacji. Zwrot pieniędzy przysługuje zawsze."""

    REFUND = "refund", "Zwrot pieniędzy"
    REPAIR = "repair", "Naprawa"
    REPLACEMENT = "replacement", "Wymiana"


class ReturnRequestStatus(models.TextChoices):
    """Stan zgłoszenia — rozpatrzone, gdy każda pozycja ma decyzję."""

    SUBMITTED = "submitted", "Zgłoszone"
    RESOLVED = "resolved", "Rozpatrzone"


class ReturnItemStatus(models.TextChoices):
    """Stan pozycji zgłoszenia; decyzję sklep podejmuje osobno dla każdej."""

    PENDING = "pending", "Oczekuje na rozpatrzenie"
    TO_AGREE = "to_agree", "Do uzgodnienia"
    ACCEPTED = "accepted", "Uwzględniona"
    REJECTED = "rejected", "Odrzucona"


class ReturnRefundStatus(models.TextChoices):
    """Stan pieniężnej części rozliczenia zwrotu (ADR 0031)."""

    NONE = "none", "Bez zwrotu pieniędzy"
    PENDING = "pending", "Zlecony u operatora"
    REFUNDED = "refunded", "Zwrócony"
    MANUAL = "manual", "Do zwrotu ręcznego"
    MANUAL_DONE = "manual_done", "Zwrócony przelewem"


OPEN_ITEM_STATUSES = frozenset({ReturnItemStatus.PENDING, ReturnItemStatus.TO_AGREE})


class ReturnRequest(TimestampedModel):
    """Zgłoszenie zwrotu wybranych pozycji doręczonego zamówienia (`CONTEXT.md`).

    Jedna podstawa na zgłoszenie — to ona wyznacza termin. Po rozpatrzeniu
    przyjęte pozycje rozlicza `services.settlement`: najpierw kupon, resztę
    pieniędzmi (ADR 0031). Wymiana to osobny etap.
    """

    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.PROTECT,
        related_name="return_requests",
    )
    reason = models.CharField(
        max_length=16,
        choices=ReturnReason.choices,
        help_text="Podstawa zwrotu — obowiązkowa",
    )
    status = models.CharField(
        max_length=16,
        choices=ReturnRequestStatus.choices,
        default=ReturnRequestStatus.SUBMITTED,
    )

    # --- Rozliczenie (ADR 0031) ------------------------------------------
    compensation_amount = MoneyAmountField(
        null=True,
        blank=True,
        editable=False,
        help_text="Zwracana kwota w groszach; pusta, dopóki nie rozliczono",
    )
    coupon = models.OneToOneField(
        "promotions.Coupon",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        editable=False,
        related_name="return_request",
        help_text="Kupon wydany z kuponowej części zwrotu",
    )
    refund_amount = MoneyAmountField(
        default=0,
        editable=False,
        help_text="Pieniężna część zwrotu w groszach",
    )
    refund_status = models.CharField(
        max_length=16,
        choices=ReturnRefundStatus.choices,
        default=ReturnRefundStatus.NONE,
        editable=False,
    )
    refund_id = models.CharField(
        max_length=255,
        blank=True,
        editable=False,
        help_text="Identyfikator zwrotu u operatora",
    )
    settled_at = models.DateTimeField(null=True, blank=True, editable=False)

    class Meta:
        verbose_name = "Zgłoszenie zwrotu"
        verbose_name_plural = "Zgłoszenia zwrotu"
        ordering = ["-created_at", "-id"]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(reason=""),
                name="return_request_reason_is_required",
            )
        ]

    def __str__(self) -> str:
        return f"Zwrot {self.pk} — {self.order.number}"  # type: ignore[missing-attribute]

    @property
    def currency(self) -> str:
        return self.order.currency  # type: ignore[missing-attribute]

    @property
    def compensation_money(self) -> Money | None:
        if self.compensation_amount is None:
            return None
        return Money(self.compensation_amount, self.currency)

    @property
    def refund_money(self) -> Money | None:
        if self.settled_at is None:
            return None
        return Money(self.refund_amount, self.currency)


class ReturnRequestItem(TimestampedModel):
    """Pozycja zgłoszenia zwrotu z decyzją sklepu.

    Para obrączek jest jedną pozycją zamówienia (ADR 0024), więc wraca
    w całości — ilość liczy pary, nie egzemplarze.
    """

    return_request = models.ForeignKey(
        ReturnRequest,
        on_delete=models.CASCADE,
        related_name="items",
    )
    order_item = models.ForeignKey(
        "orders.OrderItem",
        on_delete=models.PROTECT,
        related_name="return_items",
    )
    quantity = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    claim_request = models.CharField(
        max_length=16,
        choices=ClaimRequest.choices,
        blank=True,
        help_text="Żądanie reklamacyjne; puste przy innej podstawie",
    )
    status = models.CharField(
        max_length=16,
        choices=ReturnItemStatus.choices,
        default=ReturnItemStatus.PENDING,
    )
    restocked = models.BooleanField(
        default=False,
        help_text="Towar wrócił na stan ruchem magazynowym `return`",
    )
    decision_note = models.TextField(
        blank=True,
        help_text="Uzasadnienie decyzji — obowiązkowe przy odrzuceniu",
    )
    agreed_resolution = models.CharField(
        max_length=200,
        blank=True,
        help_text="Uzgodniona forma, np. odkup po cenie złomu (pozycja do uzgodnienia)",
    )
    agreed_amount = MoneyAmountField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Uzgodniona kwota w groszach, w walucie zamówienia",
    )
    exchange_order = models.OneToOneField(
        "orders.Order",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        editable=False,
        related_name="return_exchange_item",
        help_text="Zamówienie 0 zł wymiany na ten sam wariant (#198)",
    )
    decided_at = models.DateTimeField(null=True, blank=True, editable=False)

    class Meta:
        verbose_name = "Pozycja zgłoszenia zwrotu"
        verbose_name_plural = "Pozycje zgłoszenia zwrotu"
        ordering = ["created_at", "id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity__gte=1),
                name="return_item_quantity_is_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(agreed_amount__isnull=True)
                | models.Q(agreed_amount__gte=0),
                name="return_item_agreed_amount_is_not_negative",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.order_item} → {self.quantity}"

    @property
    def is_open(self) -> bool:
        return self.status in OPEN_ITEM_STATUSES

    @property
    def agreed_money(self) -> Money | None:
        if self.agreed_amount is None:
            return None
        return Money(self.agreed_amount, self.order_item.currency)
