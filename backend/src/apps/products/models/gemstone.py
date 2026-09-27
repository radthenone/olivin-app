from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from apps.products.models.choices import Stone
from common import TimestampedModel
from core.storage.storages import DocumentStorage

MAX_CERTIFICATE_BYTES = 10 * 1024 * 1024


def documents_storage() -> DocumentStorage:
    """Magazyn dokumentów jako wywołanie, nie instancja zapisana w polu.

    Instancja trafiłaby do migracji razem z adresem dostawcy, a ten zmienia
    się między środowiskami.
    """
    return DocumentStorage()


def validate_certificate(file) -> None:
    if file.size and file.size > MAX_CERTIFICATE_BYTES:
        raise ValidationError(
            f"Certyfikat ma {file.size // 1024 // 1024} MB — limit to "
            f"{MAX_CERTIFICATE_BYTES // 1024 // 1024} MB."
        )
    name = (file.name or "").lower()
    if not name.endswith(".pdf"):
        raise ValidationError("Certyfikat laboratorium jest dokumentem PDF.")


class Clarity(models.TextChoices):
    """Czystość w skali Gemological Institute of America."""

    FL = "FL", "FL — bez skaz"
    IF = "IF", "IF — bez skaz wewnętrznych"
    VVS1 = "VVS1", "VVS1"
    VVS2 = "VVS2", "VVS2"
    VS1 = "VS1", "VS1"
    VS2 = "VS2", "VS2"
    SI1 = "SI1", "SI1"
    SI2 = "SI2", "SI2"
    I1 = "I1", "I1"
    I2 = "I2", "I2"
    I3 = "I3", "I3"


class Colour(models.TextChoices):
    """Barwa w skali GIA: od D (bezbarwny) do Z."""

    D = "D", "D — bezbarwny"
    E = "E", "E"
    F = "F", "F"
    G = "G", "G"
    H = "H", "H"
    I = "I", "I"  # noqa: E741
    J = "J", "J"
    K = "K", "K"
    L = "L", "L"
    M = "M", "M"
    FANCY = "fancy", "Barwa fantazyjna"


class Cut(models.TextChoices):
    BRILLIANT = "brilliant", "Brylantowy"
    PRINCESS = "princess", "Princessa"
    EMERALD = "emerald", "Szmaragdowy"
    OVAL = "oval", "Owalny"
    PEAR = "pear", "Gruszka"
    MARQUISE = "marquise", "Markiza"
    CUSHION = "cushion", "Poduszka"
    ASSCHER = "asscher", "Asscher"
    RADIANT = "radiant", "Radiant"
    HEART = "heart", "Serce"
    CABOCHON = "cabochon", "Kaboszon"


class Gemstone(TimestampedModel):
    """Kamień osadzony w wariancie (`CONTEXT.md`, Gemstone).

    Wariant może mieć wiele kamieni albo żadnego. To nie jest pozycja
    kosztowa — koszt kamienia opisuje `CostComponent`; tutaj są parametry,
    które widzi klient, i certyfikat, jeśli laboratorium go wystawiło.
    """

    variant = models.ForeignKey(
        "products.ProductVariant",
        on_delete=models.CASCADE,
        related_name="gemstones",
    )
    kind = models.CharField(
        max_length=16,
        choices=Stone.choices,
        help_text="Rodzaj kamienia",
    )
    carat = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        validators=[MinValueValidator(Decimal("0.001"))],
        help_text="Masa w karatach",
    )
    clarity = models.CharField(
        max_length=4,
        choices=Clarity.choices,
        blank=True,
        help_text="Czystość; pusta, gdy nie była oznaczana",
    )
    colour = models.CharField(
        max_length=8,
        choices=Colour.choices,
        blank=True,
        help_text="Barwa; pusta, gdy nie była oznaczana",
    )
    cut = models.CharField(
        max_length=16,
        choices=Cut.choices,
        blank=True,
        help_text="Szlif; pusty, gdy nie był oznaczany",
    )
    laboratory = models.CharField(
        max_length=80,
        blank=True,
        help_text="Laboratorium, które wystawiło certyfikat",
    )
    certificate_number = models.CharField(
        max_length=64,
        blank=True,
        help_text="Numer certyfikatu nadany przez laboratorium",
    )
    certificate = models.FileField(
        storage=documents_storage,
        upload_to="certificates/",
        blank=True,
        validators=[validate_certificate],
        help_text=(
            "PDF certyfikatu. Trafia do prywatnego bucketa `documents` — "
            "klient dostaje adres podpisany na czas, nie stały odnośnik."
        ),
    )

    class Meta:
        verbose_name = "Kamień"
        verbose_name_plural = "Kamienie"
        ordering = ["-carat", "id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(carat__gt=0),
                name="gemstone_carat_is_positive",
            )
        ]

    def __str__(self) -> str:
        return f"{self.get_kind_display()} {self.carat} ct"

    @property
    def certificate_key(self) -> str:
        """Klucz dokumentu w buckecie — bez hosta i bez nazwy bucketa."""
        return self.certificate.name or ""

    @property
    def has_certificate(self) -> bool:
        return bool(self.certificate_key)

    def clean(self) -> None:
        super().clean()
        if self.has_certificate and not (self.laboratory or self.certificate_number):
            raise ValidationError(
                {
                    "laboratory": (
                        "Certyfikat bez laboratorium i bez numeru nie daje się "
                        "z niczym zestawić — podaj przynajmniej jedno."
                    )
                }
            )
