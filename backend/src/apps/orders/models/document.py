from __future__ import annotations

from django.db import models

from common import TimestampedModel


class SalesDocumentKind(models.TextChoices):
    """Rodzaj dokumentu sprzedaży (`CONTEXT.md`, SalesDocument)."""

    CONFIRMATION = "confirmation", "Potwierdzenie zamówienia"
    INVOICE = "invoice", "Faktura"
    CORRECTION = "correction", "Korekta"


# Przedrostek w oznaczeniu dokumentu — numer sam w sobie jest ciągły
# w obrębie rodzaju, więc bez przedrostka dwa dokumenty miałyby ten sam
# numer na wydruku.
DOCUMENT_PREFIXES: dict[str, str] = {
    SalesDocumentKind.CONFIRMATION: "PZ",
    SalesDocumentKind.INVOICE: "FV",
    SalesDocumentKind.CORRECTION: "KOR",
}


class DocumentCounter(models.Model):
    """Licznik numeracji w obrębie rodzaju i roku (ADR 0026).

    Osobny wiersz, a nie `max(number) + 1`: agregatu nie da się zablokować,
    więc dwa równoległe zadania policzyłyby ten sam numer. Wiersz licznika
    blokuje `select_for_update` i szereguje nadawanie numerów.
    """

    kind = models.CharField(max_length=16, choices=SalesDocumentKind.choices)
    year = models.PositiveSmallIntegerField()
    last_number = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Licznik dokumentów"
        verbose_name_plural = "Liczniki dokumentów"
        constraints = [
            models.UniqueConstraint(
                fields=["kind", "year"], name="document_counter_kind_year_unique"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.kind} {self.year}: {self.last_number}"


class SalesDocument(TimestampedModel):
    """Dokument sprzedaży wystawiony do zamówienia (`CONTEXT.md`, SalesDocument).

    Powstaje raz, na backendzie, po opłaceniu zamówienia (ADR 0026). Baza
    trzyma wyłącznie klucz obiektu w buckecie `documents` — adres podpisany
    na czas składa serializer (ADR 0025).
    """

    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.PROTECT,
        related_name="documents",
        help_text="Zamówienie, do którego wystawiono dokument",
    )
    kind = models.CharField(
        max_length=16,
        choices=SalesDocumentKind.choices,
        help_text="Rodzaj dokumentu; korekta przychodzi ze zwrotami",
    )
    number = models.PositiveIntegerField(
        help_text="Numer ciągły w obrębie rodzaju i roku",
    )
    year = models.PositiveSmallIntegerField(
        help_text="Rok numeracji — ten sam, co rok wystawienia",
    )
    return_request = models.OneToOneField(
        "orders.ReturnRequest",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="correction",
        help_text="Rozliczony zwrot, który koryguje ten dokument (tylko korekta)",
    )
    issued_on = models.DateField(help_text="Data wystawienia dokumentu")
    object_key = models.CharField(
        max_length=255,
        help_text="Klucz PDF w buckecie `documents`, bez hosta i bucketa",
    )

    class Meta:
        verbose_name = "Dokument sprzedaży"
        verbose_name_plural = "Dokumenty sprzedaży"
        ordering = ["created_at", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["kind", "year", "number"],
                name="sales_document_number_unique",
            ),
            # Potwierdzenie i faktura są jedne na zamówienie; korekt może być
            # kilka, bo przychodzą z kolejnymi zwrotami.
            models.UniqueConstraint(
                fields=["order", "kind"],
                condition=~models.Q(kind=SalesDocumentKind.CORRECTION),
                name="sales_document_once_per_order",
            ),
        ]

    def __str__(self) -> str:
        return self.reference

    @property
    def reference(self) -> str:
        """Oznaczenie z wydruku, np. `FV 12/2026`."""
        return f"{DOCUMENT_PREFIXES[self.kind]} {self.number}/{self.year}"
