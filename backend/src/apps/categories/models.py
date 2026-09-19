from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify

from common import TimestampedModel
from common.money import DEFAULT_CURRENCY, Money, MoneyAmountField

SLUG_MAX_LENGTH = 140


class Category(TimestampedModel):
    """Węzeł drzewiastej taksonomii katalogu (`CONTEXT.md`, Category).

    Drzewo jest listą sąsiedztwa — rodzic jako klucz obcy do samego siebie.
    Taksonomia sklepu jubilerskiego ma kilka poziomów i kilkadziesiąt węzłów,
    więc biblioteka do drzew (mptt, treebeard) kosztowałaby zależność i
    denormalizację, których nic tu nie zwraca: całe drzewo mieści się w jednym
    zapytaniu.

    Slug jest angielski i niezmienny. Angielskiej formy nie da się wyprowadzić
    z polskiej nazwy, więc wpisuje ją właściciel w panelu; puste pole zostaje
    wypełnione z nazwy przy pierwszym zapisie, żeby żaden węzeł nie został bez
    adresu. Po zapisaniu slug jest zablokowany — zmiana adresu opublikowanej
    kategorii to przekierowanie, nie edycja pola.
    """

    name = models.CharField(
        max_length=120,
        help_text="Nazwa kategorii po polsku, widoczna w menu sklepu",
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
    parent = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="children",
        help_text="Kategoria nadrzędna; puste oznacza korzeń drzewa",
    )
    margin_percent = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=(
            "Domyślny narzut procentowy dla wariantów w tej kategorii "
            "(ADR 0022). Wyklucza się z narzutem kwotowym."
        ),
    )
    margin_amount = MoneyAmountField(
        null=True,
        blank=True,
        help_text=(
            f"Domyślny narzut kwotowy w groszach ({DEFAULT_CURRENCY}). "
            "Wyklucza się z narzutem procentowym."
        ),
    )

    class Meta:
        verbose_name = "Kategoria"
        verbose_name_plural = "Kategorie"
        # Menu sklepu czyta się alfabetycznie, nie po dacie dodania węzła.
        ordering = ["name", "id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(margin_percent__isnull=True)
                | models.Q(margin_amount__isnull=True),
                name="category_margin_is_percent_or_amount",
            )
        ]

    def __str__(self) -> str:
        return self.name

    @property
    def margin(self) -> Money | None:
        """Narzut kwotowy jako `Money`; `None`, gdy kategoria go nie ma."""
        if self.margin_amount is None:
            return None
        return Money(self.margin_amount, DEFAULT_CURRENCY)

    def clean(self) -> None:
        super().clean()
        if self.margin_percent is not None and self.margin_amount is not None:
            raise ValidationError(
                {
                    "margin_amount": (
                        "Narzut jest procentowy albo kwotowy — nie oba naraz."
                    )
                }
            )
        if self.parent_id and self.parent_id == self.pk:
            raise ValidationError({"parent": "Kategoria nie może być swoim rodzicem."})
        if self._creates_cycle():
            raise ValidationError(
                {"parent": "Taki rodzic zamknąłby drzewo w pętlę."},
            )

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = self._available_slug(slugify(self.name))
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
                {"slug": "Slug jest niezmienny — adres kategorii już istnieje."}
            )

    def _available_slug(self, base: str) -> str:
        """Dokłada przyrostek, dopóki slug jest zajęty.

        Kolizja jest realna: „Pierścionki złote" i „Pierścionki, złote" dają
        ten sam slug, a kolumna jest unikalna.
        """
        base = base[:SLUG_MAX_LENGTH] or "category"
        candidate = base
        taken = type(self).objects.exclude(pk=self.pk)
        suffix = 2
        while taken.filter(slug=candidate).exists():
            tail = f"-{suffix}"
            candidate = f"{base[: SLUG_MAX_LENGTH - len(tail)]}{tail}"
            suffix += 1
        return candidate

    def _creates_cycle(self) -> bool:
        if not self.pk or not self.parent_id:
            return False
        ancestor_id = self.parent_id
        seen: set[object] = set()
        while ancestor_id is not None and ancestor_id not in seen:
            if ancestor_id == self.pk:
                return True
            seen.add(ancestor_id)
            ancestor_id = (
                type(self)
                .objects.filter(pk=ancestor_id)
                .values_list("parent_id", flat=True)
                .first()
            )
        return False
