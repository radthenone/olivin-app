from __future__ import annotations

import secrets
from datetime import datetime

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.functions import Mod
from django.db.models.lookups import Exact
from django.utils import timezone

from common import TimestampedModel
from common.money import CurrencyField, Money, MoneyAmountField

CODE_MAX_LENGTH = 32


class PromotionKind(models.TextChoices):
    PERCENT = "percent", "Procentowa"
    AMOUNT = "amount", "Kwotowa"


class PromotionQuerySet(models.QuerySet["Promotion"]):
    def active(self, moment: datetime | None = None) -> PromotionQuerySet:
        """Promocje, których okres obejmuje podaną chwilę (domyślnie teraz)."""
        moment = moment or timezone.now()
        return self.filter(starts_at__lte=moment).filter(
            models.Q(ends_at__isnull=True) | models.Q(ends_at__gt=moment)
        )


class Promotion(TimestampedModel):
    """Rabat obniżający cenę pozycji przed podatkiem (`CONTEXT.md`, Promotion).

    Na pozycję działa najwyżej jedna promocja — najkorzystniejsza dla klienta —
    i nigdy nie schodzi poniżej kosztu wariantu (ADR 0022, 0023). To nie jest
    forma zapłaty: tym jest kupon, liczony dopiero po promocjach.

    Zakres jest jawny: pusta lista produktów, kolekcji i kategorii nie znaczy
    „cały katalog". Zapomniane przypięcie produktów ma dać promocję, która nie
    działa nigdzie, a nie rabat na wszystko.
    """

    name = models.CharField(max_length=120, help_text="Nazwa promocji po polsku")
    kind = models.CharField(
        max_length=16,
        choices=PromotionKind.choices,
        help_text="Procentowa albo kwotowa",
    )
    value = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text=(
            "Procent obniżki (1–100) albo kwota obniżki jednego egzemplarza "
            "w groszach — zależnie od rodzaju"
        ),
    )
    currency = CurrencyField(
        help_text="Waluta kwoty obniżki i minimalnej wartości koszyka"
    )

    whole_catalog = models.BooleanField(
        default=False,
        help_text="Promocja na cały katalog — wtedy listy poniżej są pomijane",
    )
    products = models.ManyToManyField(
        "products.Product",
        related_name="promotions",
        blank=True,
        help_text="Produkty objęte promocją",
    )
    collections = models.ManyToManyField(
        "collections.Collection",
        related_name="promotions",
        blank=True,
        help_text="Kolekcje objęte promocją",
    )
    categories = models.ManyToManyField(
        "categories.Category",
        related_name="promotions",
        blank=True,
        help_text="Kategorie objęte promocją — razem z ich podkategoriami",
    )

    starts_at = models.DateTimeField(
        default=timezone.now, help_text="Początek obowiązywania"
    )
    ends_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Koniec obowiązywania; puste oznacza promocję bezterminową",
    )
    code = models.CharField(
        max_length=CODE_MAX_LENGTH,
        blank=True,
        help_text=(
            "Kod aktywujący promocję w koszyku; puste oznacza promocję "
            "działającą bez kodu. Wielkość liter nie ma znaczenia."
        ),
    )
    requires_premium = models.BooleanField(
        default=False,
        help_text=(
            "Tylko dla klientów premium. Do czasu wprowadzenia członkostwa "
            "taka promocja nie działa dla nikogo."
        ),
    )
    per_customer_limit = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Ile zamówień jednego klienta może z niej skorzystać; puste — bez limitu",
    )
    global_limit = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Ile zamówień łącznie może z niej skorzystać; puste — bez limitu",
    )
    min_cart_value = MoneyAmountField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Minimalna wartość koszyka w groszach, przed rabatami",
    )

    objects: PromotionQuerySet = PromotionQuerySet.as_manager()  # type: ignore[bad-assignment]

    class Meta:
        verbose_name = "Promocja"
        verbose_name_plural = "Promocje"
        ordering = ["-starts_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["code"],
                condition=~models.Q(code=""),
                name="promotion_code_unique",
            ),
            models.CheckConstraint(
                condition=models.Q(value__gte=1)
                & (~models.Q(kind=PromotionKind.PERCENT) | models.Q(value__lte=100)),
                name="promotion_value_within_range",
            ),
            models.CheckConstraint(
                condition=models.Q(ends_at__isnull=True)
                | models.Q(ends_at__gt=models.F("starts_at")),
                name="promotion_ends_after_start",
            ),
        ]

    def __str__(self) -> str:
        return self.name

    @property
    def min_cart_money(self) -> Money | None:
        if self.min_cart_value is None:
            return None
        return Money(self.min_cart_value, self.currency)

    def clean(self) -> None:
        super().clean()
        self.code = normalise_code(self.code)
        if self.kind == PromotionKind.PERCENT and self.value > 100:
            raise ValidationError({"value": "Procent obniżki to najwyżej 100."})
        if self.ends_at is not None and self.ends_at <= self.starts_at:
            raise ValidationError({"ends_at": "Koniec musi być po początku."})

    def save(self, *args, **kwargs) -> None:
        self.code = normalise_code(self.code)
        super().save(*args, **kwargs)


def normalise_code(code: str) -> str:
    """Kod porównywany bez względu na wielkość liter i spacje wokół."""
    return code.strip().upper()


class PromotionRedemption(TimestampedModel):
    """Zastosowanie promocji w zamówieniu wraz z naliczoną kwotą (`CONTEXT.md`).

    Jeden wiersz na promocję i zamówienie — kwota to suma rabatów tej promocji
    na wszystkich pozycjach. Z tych wierszy liczą się limity użyć; wiersze
    zamówień anulowanych nie zużywają limitu.
    """

    promotion = models.ForeignKey(
        Promotion,
        on_delete=models.PROTECT,
        related_name="redemptions",
    )
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="promotion_redemptions",
    )
    amount = MoneyAmountField(
        validators=[MinValueValidator(0)],
        help_text="Suma rabatu tej promocji w zamówieniu, w walucie zamówienia",
    )

    class Meta:
        verbose_name = "Zastosowanie promocji"
        verbose_name_plural = "Zastosowania promocji"
        constraints = [
            models.UniqueConstraint(
                fields=["promotion", "order"],
                name="promotion_redemption_unique_per_order",
            ),
            models.CheckConstraint(
                condition=models.Q(amount__gte=0),
                name="promotion_redemption_amount_is_not_negative",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.promotion} → {self.order}"


# Nominał kuponu to wielokrotność 10 zł, w groszach (ADR 0011).
COUPON_NOMINAL_STEP = 1000

# Kod kuponu nadaje sklep: bez zer, jedynek, „I" i „O", jak numer zamówienia.
_COUPON_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
_COUPON_CODE_LENGTH = 12


def new_coupon_code() -> str:
    return "".join(secrets.choice(_COUPON_ALPHABET) for _ in range(_COUPON_CODE_LENGTH))


def twelve_months_later(moment: datetime | None = None) -> datetime:
    """Ta sama chwila rok później; 29 lutego przechodzi na 28."""
    moment = moment or timezone.now()
    try:
        return moment.replace(year=moment.year + 1)
    except ValueError:
        return moment.replace(year=moment.year + 1, day=28)


def _validate_nominal(value: int) -> None:
    if value <= 0 or value % COUPON_NOMINAL_STEP:
        raise ValidationError("Nominał kuponu to dodatnia wielokrotność 10 zł.")


class CouponStatus(models.TextChoices):
    ISSUED = "issued", "Wydany"
    REDEEMED = "redeemed", "Wykorzystany"
    EXPIRED = "expired", "Wygasły"


class CouponSource(models.TextChoices):
    CAMPAIGN = "campaign", "Kampania"
    RETURN = "return", "Zwrot"


class Coupon(TimestampedModel):
    """Jednorazowy kupon — forma zapłaty za towar (`CONTEXT.md`, Coupon).

    Pokrywa towar po promocjach, nigdy dostawę; niewykorzystana część
    nominału przepada (ADR 0011, 0023). Nie jest rabatem: nie obniża podstawy
    opodatkowania, tylko rozlicza zapłatę (ADR 0014).
    """

    code = models.CharField(
        max_length=CODE_MAX_LENGTH,
        unique=True,
        default=new_coupon_code,
        help_text="Kod nadany przez sklep. Wielkość liter nie ma znaczenia.",
    )
    nominal = MoneyAmountField(
        validators=[_validate_nominal],
        help_text="Nominał w groszach — wielokrotność 10 zł (1000 gr)",
    )
    currency = CurrencyField(help_text="Waluta nominału")
    expires_at = models.DateTimeField(
        default=twelve_months_later,
        help_text="Koniec ważności — 12 miesięcy od wydania",
    )
    status = models.CharField(
        max_length=16,
        choices=CouponStatus.choices,
        default=CouponStatus.ISSUED,
    )
    source = models.CharField(
        max_length=16,
        choices=CouponSource.choices,
        default=CouponSource.CAMPAIGN,
        help_text="Skąd kupon: kampania marketingowa albo przyjęty zwrot",
    )

    class Meta:
        verbose_name = "Kupon"
        verbose_name_plural = "Kupony"
        ordering = ["-created_at", "-id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    Exact(Mod("nominal", COUPON_NOMINAL_STEP), 0), nominal__gt=0
                ),
                name="coupon_nominal_multiple_of_ten_zloty",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.code} ({self.nominal_money})"

    @property
    def nominal_money(self) -> Money:
        return Money(self.nominal, self.currency)

    def is_usable(self, moment: datetime | None = None) -> bool:
        """Wydany i w terminie — sam status nie wystarcza, zadanie biega raz na dobę."""
        moment = moment or timezone.now()
        return self.status == CouponStatus.ISSUED and self.expires_at > moment

    def clean(self) -> None:
        super().clean()
        self.code = normalise_code(self.code)

    def save(self, *args, **kwargs) -> None:
        try:
            _validate_nominal(self.nominal)
        except ValidationError as error:
            raise ValidationError({"nominal": error.messages}) from error
        self.code = normalise_code(self.code)
        super().save(*args, **kwargs)


class CouponRedemption(TimestampedModel):
    """Użycie kuponu w zamówieniu z faktycznie naliczoną kwotą (`CONTEXT.md`).

    Zdarzenie, nie saldo (ADR 0014): wiersz zostaje także wtedy, gdy
    nieopłacone zamówienie anulowano i kupon wrócił do użycia.
    """

    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.PROTECT,
        related_name="redemptions",
    )
    order = models.OneToOneField(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="coupon_redemption",
    )
    amount = MoneyAmountField(
        validators=[MinValueValidator(0)],
        help_text="Kwota pokryta kuponem — najwyżej nominał, reszta przepada",
    )

    class Meta:
        verbose_name = "Użycie kuponu"
        verbose_name_plural = "Użycia kuponów"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gte=0),
                name="coupon_redemption_amount_is_not_negative",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.coupon} → {self.order}"
