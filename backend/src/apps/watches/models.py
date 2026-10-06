from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from common import TimestampedModel
from common.money import CurrencyField, MoneyAmountField


class WatchKind(models.TextChoices):
    """Rodzaj obserwowania (`CONTEXT.md`, Watch)."""

    RESTOCK = "restock", "Powrót na stan"
    PRICE_DROP = "price_drop", "Spadek ceny"


class WatchStatus(models.TextChoices):
    """Status prośby (`CONTEXT.md`, Watch)."""

    ACTIVE = "active", "Aktywna"
    SENT = "sent", "Wysłana"


class WatchQuerySet(models.QuerySet["Watch"]):
    def active(self) -> WatchQuerySet:
        """Prośby czekające na wyzwalacz — jednorazowe, wygasają po wysłaniu."""
        return self.filter(status=WatchStatus.ACTIVE)


class Watch(TimestampedModel):
    """Jednorazowa prośba o powiadomienie o wariancie (`CONTEXT.md`, Watch).

    Dotyczy wariantu, bo to on ma stan i cenę. Produkt na zamówienie można
    obserwować tylko pod kątem ceny — nie ma stanu, więc powrót na stan
    nigdy by nie nastąpił (ADR 0024). „Stanieje” oznacza obniżkę `Price`
    wariantu — promocje się nie liczą.

    Rekord wygasa po wysłaniu powiadomienia (status `sent`). Usunięcie konta
    kasuje obserwowane: klucz do użytkownika jest `CASCADE`, a przyszła
    anonimizacja (`CONTEXT.md`, Account anonymisation) ma usunąć wpisy
    użytkownika razem z danymi osobowymi.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="watches",
        help_text="Klient obserwujący wariant",
    )
    variant = models.ForeignKey(
        "products.ProductVariant",
        on_delete=models.CASCADE,
        related_name="watches",
        help_text="Obserwowany wariant",
    )
    kind = models.CharField(
        max_length=16,
        choices=WatchKind.choices,
        help_text="Rodzaj wyzwalacza",
    )
    price_at_watch = MoneyAmountField(
        null=True,
        blank=True,
        help_text="Cena w chwili zapisu (grosze) — tylko dla spadku ceny",
    )
    currency = CurrencyField()
    status = models.CharField(
        max_length=16,
        choices=WatchStatus.choices,
        default=WatchStatus.ACTIVE,
        help_text="Aktywna czeka; wysłana wygasła",
    )

    objects: WatchQuerySet = WatchQuerySet.as_manager()  # type: ignore[bad-assignment]

    class Meta:
        verbose_name = "Obserwowany wariant"
        verbose_name_plural = "Obserwowane warianty"
        ordering = ["-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "variant", "kind"],
                condition=models.Q(status="active"),
                name="watch_one_active_per_user_variant_kind",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(kind="price_drop", price_at_watch__isnull=False)
                    | models.Q(kind="restock", price_at_watch__isnull=True)
                ),
                name="watch_price_only_for_price_drop",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.user} — {self.variant} ({self.kind})"

    def clean(self) -> None:
        super().clean()
        variant = self.variant
        product = getattr(variant, "product", None)
        if (
            product is not None
            and getattr(product, "is_made_to_order", False)
            and self.kind == WatchKind.RESTOCK
        ):
            raise ValidationError(
                {"kind": "Produkt na zamówienie można obserwować tylko pod kątem ceny."}
            )

    def mark_sent(self) -> None:
        """Wygasza prośbę po wysłaniu powiadomienia."""
        if self.status != WatchStatus.ACTIVE:
            return
        self.status = WatchStatus.SENT
        self.save(update_fields=["status", "updated_at"])
