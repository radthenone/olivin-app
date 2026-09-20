from __future__ import annotations

from typing import Any

from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ValidationError
from django.db import models, transaction

from common import TimestampedModel
from core.storage.storages import OriginalStorage

# Szerokości, w jakich sklep pokazuje zdjęcie: miniatura na liście, karta
# produktu i podgląd po powiększeniu (ADR 0025).
RENDITION_WIDTHS: tuple[int, ...] = (400, 800, 1600)

# Jakość WebP. Poniżej osiemdziesiątki widać artefakty na gładkim metalu,
# powyżej osiemdziesięciu pięciu plik rośnie bez widocznego zysku.
WEBP_QUALITY = 82

MAX_ORIGINAL_BYTES = 10 * 1024 * 1024

CROP_KEYS = ("x", "y", "width", "height")


def originals_storage() -> OriginalStorage:
    """Magazyn oryginałów jako wywołanie, a nie instancja w polu.

    Instancja zapisana wprost w polu trafiłaby do migracji razem z adresem
    dostawcy, a ten zmienia się między środowiskami.
    """
    return OriginalStorage()


def validate_original_size(file: Any) -> None:
    if file.size and file.size > MAX_ORIGINAL_BYTES:
        raise ValidationError(
            f"Oryginał ma {file.size // 1024 // 1024} MB — limit to "
            f"{MAX_ORIGINAL_BYTES // 1024 // 1024} MB."
        )


class ImageStatus(models.TextChoices):
    PROCESSING = "processing", "W przetwarzaniu"
    READY = "ready", "Gotowe"


class ProductImageQuerySet(models.QuerySet["ProductImage"]):
    def ready(self) -> ProductImageQuerySet:
        return self.filter(status=ImageStatus.READY)


class ProductImage(TimestampedModel):
    """Zdjęcie produktu albo jego wariantu (`CONTEXT.md`, ProductImage).

    Oryginał zostaje w prywatnym buckecie, żeby zmiana kadru nie wymagała
    ponownego wgrania (ADR 0025). Rozmiary do pokazania powstają w zadaniu
    w tle i lądują w buckecie publicznym; do czasu ich powstania zdjęcie ma
    status `processing` i nie wychodzi przez API — pół galerii jest gorsze
    niż galeria o jedno zdjęcie krótsza.
    """

    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="images",
    )
    variant = models.ForeignKey(
        "products.ProductVariant",
        on_delete=models.CASCADE,
        related_name="images",
        null=True,
        blank=True,
        help_text=(
            "Wariant, którego wygląd zdjęcie różnicuje. Puste oznacza zdjęcie "
            "całego produktu."
        ),
    )
    position = models.PositiveSmallIntegerField(
        default=0,
        help_text="Kolejność w galerii; mniejsza liczba wcześniej",
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="Zdjęcie główne produktu — jedno na produkt",
    )
    alt_text = models.CharField(
        max_length=200,
        blank=True,
        help_text="Opis alternatywny po polsku, dla czytników ekranu i SEO",
    )
    original = models.FileField(
        storage=originals_storage,
        upload_to="uploads/",
        validators=[validate_original_size],
        help_text=(
            f"Oryginał zdjęcia, najwyżej "
            f"{MAX_ORIGINAL_BYTES // 1024 // 1024} MB. Zostaje zachowany, "
            "żeby zmiana kadru nie wymagała ponownego wgrania."
        ),
    )
    crop = models.JSONField(
        null=True,
        blank=True,
        help_text=(
            'Prostokąt kadru względem oryginału: {"x": 0, "y": 0, '
            '"width": 1000, "height": 1000}. Puste oznacza całe zdjęcie.'
        ),
    )
    renditions = models.JSONField(
        default=dict,
        blank=True,
        editable=False,
        help_text="Klucze gotowych rozmiarów w buckecie publicznym",
    )
    status = models.CharField(
        max_length=16,
        choices=ImageStatus.choices,
        default=ImageStatus.PROCESSING,
        editable=False,
        help_text="Zdjęcie w przetwarzaniu nie wychodzi przez API",
    )

    # Tłumaczenia jako relacja, żeby `prefetch_related` je pobrał
    # razem z obiektem — inaczej każde pole dobijałoby bazę.
    translations = GenericRelation(
        "translations.Translation",
        content_type_field="content_type",
        object_id_field="object_id",
    )

    objects: ProductImageQuerySet = ProductImageQuerySet.as_manager()  # type: ignore[bad-assignment]

    class Meta:
        verbose_name = "Zdjęcie produktu"
        verbose_name_plural = "Zdjęcia produktu"
        ordering = ["position", "created_at", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["product"],
                condition=models.Q(is_primary=True),
                name="product_image_single_primary_per_product",
            )
        ]
        indexes = [models.Index(fields=["product", "status"])]

    def __str__(self) -> str:
        return f"{self.product.name} #{self.position}"

    @property
    def original_key(self) -> str:
        """Klucz oryginału w buckecie — bez hosta i bez nazwy bucketa."""
        return self.original.name or ""

    def clean(self) -> None:
        super().clean()
        self._reject_variant_from_another_product()
        self._reject_malformed_crop()

    def save(self, *args, **kwargs) -> None:
        self._reject_malformed_crop()
        needs_processing = self._needs_processing()
        if needs_processing:
            self.status = ImageStatus.PROCESSING
        super().save(*args, **kwargs)
        if needs_processing:
            self._queue_processing()

    def _needs_processing(self) -> bool:
        """Nowe zdjęcie albo zmieniony kadr — w obu wypadkach to samo zadanie.

        Zmiana kadru nie wymaga ponownego wgrania: zadanie tnie zachowany
        oryginał (ADR 0025).
        """
        if self.pk is None:
            return True
        stored = (
            type(self)
            .objects.filter(pk=self.pk)
            .values("crop", "original", "status")
            .first()
        )
        if stored is None:
            return True
        return (
            stored["crop"] != self.crop
            or stored["original"] != self.original.name
            or stored["status"] != ImageStatus.READY
        )

    def _queue_processing(self) -> None:
        from apps.products.tasks import render_product_image

        transaction.on_commit(
            lambda: render_product_image.delay(str(self.pk))  # type: ignore[missing-attribute]
        )

    def _reject_variant_from_another_product(self) -> None:
        if self.variant_id is None:  # type: ignore[missing-attribute]
            return
        if self.variant.product_id != self.product_id:  # type: ignore[missing-attribute]
            raise ValidationError(
                {"variant": "Wariant należy do innego produktu niż to zdjęcie."}
            )

    def _reject_malformed_crop(self) -> None:
        if self.crop is None:
            return
        if not isinstance(self.crop, dict) or set(self.crop) != set(CROP_KEYS):
            raise ValidationError(
                {"crop": f"Kadr wymaga dokładnie kluczy: {', '.join(CROP_KEYS)}."}
            )
        for key in CROP_KEYS:
            value = self.crop[key]
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValidationError(
                    {
                        "crop": (
                            f"Wartość {key} musi być liczbą całkowitą "
                            "nie mniejszą niż zero."
                        )
                    }
                )
        if self.crop["width"] == 0 or self.crop["height"] == 0:
            raise ValidationError(
                {"crop": "Kadr o zerowej szerokości albo wysokości nic nie kadruje."}
            )
