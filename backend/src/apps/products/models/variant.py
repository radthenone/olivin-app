from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.functions import Coalesce

from apps.products.models.choices import Length, MetalColor, RingSize, Stone
from common import TimestampedModel
from common.money import CurrencyField, Money, MoneyAmountField

# Nazwa adnotacji musi się różnić od property `effective_price`: Django
# przypisuje adnotacje przez `setattr`, a property bez settera to wywraca.
EFFECTIVE_PRICE = "effective_price_amount"


class ProductVariantQuerySet(models.QuerySet["ProductVariant"]):
    def with_effective_price(self) -> ProductVariantQuerySet:
        """Dokłada cenę, którą widzi klient: ręczna ma pierwszeństwo.

        Liczone w bazie, a nie w Pythonie, bo po tej samej wartości idzie
        sortowanie listy produktów i wybór najtańszego wariantu.
        """
        return self.annotate(**{EFFECTIVE_PRICE: Coalesce("manual_price", "price")})


class ProductVariant(TimestampedModel):
    """Kupowalny egzemplarz produktu (`CONTEXT.md`, ProductVariant).

    Wariant nosi cenę, stawkę podatku i stan magazynowy — produkt żadnej
    z tych rzeczy nie ma. Cena jest zapisana w kolumnie, a nie liczona przy
    odczycie, bo po niej filtrujemy i sortujemy listę (ADR 0022).
    """

    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="variants",
    )
    sku = models.CharField(
        max_length=64,
        unique=True,
        help_text="Oznaczenie magazynowe wariantu, unikalne w całym katalogu",
    )
    metal_color = models.CharField(
        max_length=16,
        choices=MetalColor.choices,
        help_text="Kolor kruszcu",
    )
    size = models.CharField(
        max_length=2,
        choices=RingSize.choices,
        blank=True,
        help_text="Rozmiar pierścionka; puste dla wyrobów bez rozmiaru",
    )
    length = models.CharField(
        max_length=2,
        choices=Length.choices,
        blank=True,
        help_text="Długość w centymetrach; puste dla wyrobów bez długości",
    )
    stone = models.CharField(
        max_length=16,
        choices=Stone.choices,
        blank=True,
        help_text="Rodzaj kamienia; puste dla wyrobu bez kamienia",
    )
    metal_weight_grams = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        validators=[MinValueValidator(Decimal("0.001"))],
        help_text="Masa kruszcu w gramach — podstawa składnika kruszcowego ceny",
    )
    price = MoneyAmountField(
        validators=[MinValueValidator(0)],
        help_text="Cena brutto w groszach, wyliczona ze wzoru (ADR 0022)",
    )
    manual_price = MoneyAmountField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text=(
            "Cena brutto wpisana ręcznie; ma pierwszeństwo przed wyliczoną. "
            "Służy wyprzedaży, nie codziennej wycenie."
        ),
    )
    currency = CurrencyField()
    vat_rate = models.DecimalField(
        max_digits=4,
        decimal_places=4,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0"))],
        help_text=(
            "Stawka podatku jako ułamek, np. 0.2300. Pusta wyłącznie przy zwolnieniu."
        ),
    )
    is_vat_exempt = models.BooleanField(
        default=False,
        help_text=(
            "Zwolnienie przedmiotowe — złoto inwestycyjne. Nie jest stawką "
            "zerową, tylko osobnym bytem (ADR 0013)."
        ),
    )
    vat_exemption_basis = models.CharField(
        max_length=200,
        blank=True,
        help_text="Podstawa prawna zwolnienia; wymagana przy zwolnieniu",
    )

    # Patrz komentarz przy `Product.objects` — ten sam powód.
    objects: ProductVariantQuerySet = ProductVariantQuerySet.as_manager()  # type: ignore[bad-assignment]

    class Meta:
        verbose_name = "Wariant produktu"
        verbose_name_plural = "Warianty produktu"
        ordering = ["sku"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(is_vat_exempt=True, vat_rate__isnull=True)
                    | models.Q(is_vat_exempt=False, vat_rate__isnull=False)
                ),
                name="variant_exemption_excludes_vat_rate",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(is_vat_exempt=False) | ~models.Q(vat_exemption_basis="")
                ),
                name="variant_exemption_has_legal_basis",
            ),
            # Walidatory pól działają wyłącznie w `full_clean()`, więc zapis
            # programowy — import, `bulk_create`, przyszłe przeliczenie ceny
            # z ADR 0022 — przepuściłby kwotę ujemną. Próg kosztowy to osobna
            # sprawa; tutaj chodzi o to, żeby cena w ogóle była liczbą, która
            # ma sens.
            models.CheckConstraint(
                condition=models.Q(price__gte=0),
                name="variant_price_is_not_negative",
            ),
            models.CheckConstraint(
                condition=models.Q(manual_price__isnull=True)
                | models.Q(manual_price__gte=0),
                name="variant_manual_price_is_not_negative",
            ),
            models.CheckConstraint(
                condition=models.Q(metal_weight_grams__gt=0),
                name="variant_metal_weight_is_positive",
            ),
        ]

    def __str__(self) -> str:
        return self.sku

    @property
    def price_money(self) -> Money:
        """Cena wyliczona ze wzoru, bez względu na cenę ręczną."""
        return Money(self.price, self.currency)

    @property
    def effective_price(self) -> Money:
        """Cena, którą widzi klient — ręczna ma pierwszeństwo (ADR 0022)."""
        amount = self.price if self.manual_price is None else self.manual_price
        return Money(amount, self.currency)

    def clean(self) -> None:
        super().clean()
        self._reject_vat_mismatch()

    def save(self, *args, **kwargs) -> None:
        self._reject_vat_mismatch()
        super().save(*args, **kwargs)

    def _reject_vat_mismatch(self) -> None:
        if self.is_vat_exempt:
            if self.vat_rate is not None:
                raise ValidationError(
                    {
                        "vat_rate": (
                            "Zwolnienie nie jest stawką — zostaw stawkę pustą "
                            "(ADR 0013)."
                        )
                    }
                )
            if not self.vat_exemption_basis:
                raise ValidationError(
                    {
                        "vat_exemption_basis": (
                            "Zwolnienie wymaga podstawy prawnej — bez niej nie "
                            "da się go wykazać w ewidencji."
                        )
                    }
                )
            return

        if self.vat_rate is None:
            raise ValidationError(
                {"vat_rate": "Wariant bez zwolnienia musi mieć stawkę podatku."}
            )
        if self.vat_exemption_basis:
            raise ValidationError(
                {
                    "vat_exemption_basis": (
                        "Podstawa zwolnienia przy wariancie ze stawką jest "
                        "sprzecznością."
                    )
                }
            )
