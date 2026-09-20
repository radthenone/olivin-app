from __future__ import annotations

from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ValidationError
from django.db import models

from common import TimestampedModel
from common.slugs import SLUG_MAX_LENGTH, slug_base, unique_slug


class Collection(TimestampedModel):
    """Grupa marketingowa przecinająca kategorie (`CONTEXT.md`, Collection).

    Jedyny przekrój katalogu poza kategorią i cechami wariantu — wolnych
    tagów nie ma. Produkt należy do jednej kategorii, ale do dowolnie wielu
    kolekcji, więc relacja jest wiele-do-wielu, a nie kluczem obcym.

    Slug jest niezmienny od pierwszego zapisu, tak samo jak w kategorii:
    kolekcja nie ma stanu roboczego, powstaje od razu jako adres kampanii.
    """

    name = models.CharField(
        max_length=120,
        help_text="Nazwa kolekcji po polsku, widoczna w sklepie",
    )
    description = models.TextField(
        blank=True,
        help_text="Opis kampanii albo sezonu po polsku",
    )
    slug = models.SlugField(
        max_length=SLUG_MAX_LENGTH,
        unique=True,
        blank=True,
        help_text=(
            "Angielski identyfikator w adresie. Puste pole zostanie wypełnione "
            "z nazwy przy zapisie. Po zapisaniu nie da się go zmienić."
        ),
    )
    products = models.ManyToManyField(
        "products.Product",
        related_name="collections",
        blank=True,
        help_text="Produkty przypięte do kolekcji; mogą być z różnych kategorii",
    )

    # Tłumaczenia jako relacja, żeby `prefetch_related` je pobrał
    # razem z obiektem — inaczej każde pole dobijałoby bazę.
    translations = GenericRelation(
        "translations.Translation",
        content_type_field="content_type",
        object_id_field="object_id",
    )

    class Meta:
        verbose_name = "Kolekcja"
        verbose_name_plural = "Kolekcje"
        ordering = ["name", "id"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = unique_slug(
                type(self), slug_base(self.name, "collection"), self.pk
            )
        else:
            self._reject_slug_change()
        super().save(*args, **kwargs)

    def _reject_slug_change(self) -> None:
        if not self.pk:
            return
        stored = (
            type(self).objects.filter(pk=self.pk).values_list("slug", flat=True).first()
        )
        if stored and stored != self.slug:
            raise ValidationError(
                {"slug": "Slug jest niezmienny — adres kolekcji już istnieje."}
            )
