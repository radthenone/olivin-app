from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify

from apps.categories.models import SLUG_MAX_LENGTH, polish_to_ascii
from apps.products.models.choices import Fineness, Material, ProductStatus
from common import TimestampedModel


class ProductQuerySet(models.QuerySet["Product"]):
    def published(self) -> ProductQuerySet:
        return self.filter(status=ProductStatus.PUBLISHED)


class Product(TimestampedModel):
    """Model biżuterii jako pozycja katalogowa (`CONTEXT.md`, Product).

    Nie ma ceny ani stanu magazynowego — obie rzeczy należą do wariantu, bo to
    on jest kupowany. Status rozstrzyga widoczność: szkic nie istnieje dla
    sklepu pod żadnym adresem.

    Slug jest zamrażany dopiero przy publikacji, a nie przy pierwszym zapisie
    jak w kategorii: szkic nie ma jeszcze adresu, pod którym ktoś mógłby wejść,
    więc póki trwa przygotowanie, nazwę w adresie wolno poprawiać.
    """

    name = models.CharField(
        max_length=200,
        help_text="Nazwa produktu po polsku",
    )
    description = models.TextField(
        blank=True,
        help_text="Opis produktu po polsku",
    )
    slug = models.SlugField(
        max_length=SLUG_MAX_LENGTH,
        unique=True,
        blank=True,
        help_text=(
            "Angielski identyfikator w adresie. Puste pole zostanie wypełnione "
            "z nazwy przy zapisie. Po publikacji nie da się go zmienić."
        ),
    )
    category = models.ForeignKey(
        "categories.Category",
        on_delete=models.PROTECT,
        related_name="products",
        help_text="Kategoria-liść, czyli węzeł bez podkategorii",
    )
    material = models.CharField(
        max_length=16,
        choices=Material.choices,
        help_text="Kruszec, z którego wykonany jest wyrób",
    )
    fineness = models.CharField(
        max_length=3,
        choices=Fineness.choices,
        help_text="Próba kruszcu",
    )
    status = models.CharField(
        max_length=16,
        choices=ProductStatus.choices,
        default=ProductStatus.DRAFT,
        help_text="Tylko produkt opublikowany jest widoczny w sklepie",
    )
    is_made_to_order = models.BooleanField(
        default=False,
        help_text=(
            "Wyrób wytwarzany po złożeniu zamówienia (ADR 0024). Nie ma stanu "
            "magazynowego, ma za to czas realizacji."
        ),
    )
    production_time_days = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Czas realizacji w dniach; wymagany przy produkcie na zamówienie",
    )

    # `as_manager()` zwraca menedżera przekazującego metody queryu dalej, ale
    # stuby opisują `objects` jako `Manager[Self]` i gubią `published()`.
    # Adnotacja typem queryu jest drobną nieścisłością co do klasy obiektu,
    # za to prawdą o tym, co na nim wolno wywołać.
    objects: ProductQuerySet = ProductQuerySet.as_manager()  # type: ignore[bad-assignment]

    class Meta:
        verbose_name = "Produkt"
        verbose_name_plural = "Produkty"
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["status"])]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(is_made_to_order=True, production_time_days__isnull=False)
                    | models.Q(
                        is_made_to_order=False, production_time_days__isnull=True
                    )
                ),
                name="product_made_to_order_has_production_time",
            )
        ]

    def __str__(self) -> str:
        return self.name

    @property
    def is_published(self) -> bool:
        return self.status == ProductStatus.PUBLISHED

    def clean(self) -> None:
        super().clean()
        self._reject_non_leaf_category()
        self._reject_production_time_mismatch()

    def save(self, *args, **kwargs) -> None:
        self._reject_production_time_mismatch()
        if not self.slug:
            self.slug = self._available_slug(slugify(polish_to_ascii(self.name)))
        else:
            self._reject_slug_change_after_publication()
        super().save(*args, **kwargs)

    def _reject_non_leaf_category(self) -> None:
        """Produkt należy do jednej kategorii liścia (`CONTEXT.md`, Category).

        Produkt w węźle pośrednim pojawiłby się w menu obok podkategorii,
        a nie w żadnej z nich.
        """
        # Stuby nie generują kolumny `<fk>_id`, a sięgnięcie po sam `category`
        # na modelu bez kategorii rzuciłoby wyjątkiem zamiast wyjść z metody.
        if self.category_id is None:  # type: ignore[missing-attribute]
            return
        has_children = self.category.children.exists()
        if has_children:
            raise ValidationError(
                {"category": "Produkt należy do kategorii-liścia, bez podkategorii."}
            )

    def _reject_production_time_mismatch(self) -> None:
        if self.is_made_to_order and self.production_time_days is None:
            raise ValidationError(
                {
                    "production_time_days": (
                        "Produkt na zamówienie musi mieć czas realizacji."
                    )
                }
            )
        if not self.is_made_to_order and self.production_time_days is not None:
            raise ValidationError(
                {
                    "production_time_days": (
                        "Czas realizacji ma sens wyłącznie przy produkcie "
                        "na zamówienie."
                    )
                }
            )

    def _reject_slug_change_after_publication(self) -> None:
        if not self.pk:
            return
        stored = (
            type(self).objects.filter(pk=self.pk).values_list("slug", "status").first()
        )
        if stored is None:
            return
        stored_slug, stored_status = stored
        if stored_status == ProductStatus.PUBLISHED and stored_slug != self.slug:
            raise ValidationError(
                {
                    "slug": (
                        "Slug opublikowanego produktu jest niezmienny — "
                        "zmiana adresu to przekierowanie, nie edycja pola."
                    )
                }
            )

    def _available_slug(self, base: str) -> str:
        base = base[:SLUG_MAX_LENGTH] or "product"
        candidate = base
        taken = type(self).objects.exclude(pk=self.pk)
        suffix = 2
        while taken.filter(slug=candidate).exists():
            tail = f"-{suffix}"
            candidate = f"{base[: SLUG_MAX_LENGTH - len(tail)]}{tail}"
            suffix += 1
        return candidate
