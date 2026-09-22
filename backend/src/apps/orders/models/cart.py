from __future__ import annotations

from datetime import datetime

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from apps.products.models.choices import RingSize
from common import TimestampedModel
from common.money import Money

# Limit sztuk na pozycję (`.ai/project.md`). Pracownia jubilerska nie sprzedaje
# hurtowo, a dziesięć tych samych obrączek to prędzej pomyłka niż zamówienie.
MAX_ITEM_QUANTITY = 5

# Grawerunek mieści się na obrączce, nie na tabliczce — długość jest realna,
# a nie techniczna (ADR 0018).
ENGRAVING_MAX_LENGTH = 50

# Koszyk gościa bez aktywności przez miesiąc znika razem z tokenem.
GUEST_CART_TTL_DAYS = 30


class CartQuerySet(models.QuerySet["Cart"]):
    def guest(self) -> CartQuerySet:
        return self.filter(user__isnull=True)

    def inactive_since(self, moment: datetime) -> CartQuerySet:
        return self.filter(last_activity_at__lt=moment)


class Cart(TimestampedModel):
    """Koszyk klienta trzymany na backendzie (`CONTEXT.md`, Cart).

    Należy do użytkownika **albo** do gościa identyfikowanego tokenem, nigdy
    do obu (ADR 0030). Koszyk żyje po stronie sklepu, bo to sklep zna ceny,
    dostępność i promocje — koszyk w przeglądarce pokazywałby kwoty sprzed
    ostatniej zmiany cennika i nie przechodziłby między urządzeniami.
    """

    user = models.OneToOneField(
        "accounts.CustomUser",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="cart",
        help_text="Zalogowany właściciel koszyka; pusty przy koszyku gościa",
    )
    session_key = models.CharField(
        max_length=64,
        blank=True,
        help_text=(
            "Token koszyka gościa wydany przez backend i odsyłany nagłówkiem "
            "`X-Cart-Token`; pusty przy koszyku konta"
        ),
    )
    last_activity_at = models.DateTimeField(
        default=timezone.now,
        help_text=(
            "Ostatnia zmiana w koszyku. Koszyk gościa bez aktywności przez "
            f"{GUEST_CART_TTL_DAYS} dni jest kasowany zadaniem okresowym."
        ),
    )

    objects: CartQuerySet = CartQuerySet.as_manager()  # type: ignore[bad-assignment]

    class Meta:
        verbose_name = "Koszyk"
        verbose_name_plural = "Koszyki"
        ordering = ["-last_activity_at", "-id"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(user__isnull=False, session_key="")
                    | models.Q(user__isnull=True) & ~models.Q(session_key="")
                ),
                name="cart_owner_is_user_xor_session_key",
            ),
            # Warunkowo, bo koszyków kont z pustym tokenem jest wiele.
            models.UniqueConstraint(
                fields=["session_key"],
                condition=~models.Q(session_key=""),
                name="cart_session_key_unique",
            ),
        ]

    def __str__(self) -> str:
        owner = self.user.email if self.user_id is not None else "gość"  # type: ignore[missing-attribute]
        return f"Koszyk ({owner})"

    @property
    def is_guest(self) -> bool:
        return self.user_id is None  # type: ignore[missing-attribute]

    @property
    def item_count(self) -> int:
        """Liczba pozycji, nie sztuk — para obrączek jest jedną pozycją (ADR 0024)."""
        return self.items.count()  # type: ignore[missing-attribute]

    def touch(self) -> None:
        """Odsuwa termin sprzątania koszyka gościa o kolejne dni bezczynności."""
        self.last_activity_at = timezone.now()
        self.save(update_fields=["last_activity_at", "updated_at"])

    def clean(self) -> None:
        super().clean()
        self._reject_ambiguous_owner()

    def save(self, *args, **kwargs) -> None:
        self._reject_ambiguous_owner()
        super().save(*args, **kwargs)

    def _reject_ambiguous_owner(self) -> None:
        # Stuby nie generują kolumny `<fk>_id` — patrz `Consent._reject_ambiguous_subject`.
        has_user = self.user_id is not None  # type: ignore[missing-attribute]
        has_token = bool(self.session_key)
        if has_user and has_token:
            raise ValidationError(
                {"session_key": "Koszyk konta nie ma osobnego tokenu gościa."}
            )
        if not has_user and not has_token:
            raise ValidationError(
                {"session_key": "Koszyk gościa wymaga tokenu, koszyk klienta — konta."}
            )


class CartItem(TimestampedModel):
    """Pozycja koszyka (`CONTEXT.md`, CartItem).

    Nie zamraża ceny: koszyk pokazuje cenę z dnia oglądania, a kopia trafia
    dopiero do zamówienia (ADR 0010). Dwie pozycje na ten sam wariant
    z różnym grawerunkiem to dwie różne pozycje i nie wolno ich scalić —
    grawer czyni wyrób innym towarem (ADR 0018).

    Para obrączek jest jedną pozycją z dwoma egzemplarzami o osobnych
    rozmiarach (ADR 0024): klient kupuje ją jako całość i tak samo zwraca.
    Parę da się złożyć wyłącznie z wyrobu na zamówienie — wyrób magazynowy
    w drugim rozmiarze jest innym wariantem, z własnym stanem, więc para
    z niego nie miałaby z czego zdjąć drugiego egzemplarza.
    """

    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items",
    )
    variant = models.ForeignKey(
        "products.ProductVariant",
        on_delete=models.PROTECT,
        related_name="cart_items",
        help_text="Kupowany wariant — jedyna rzecz, którą da się dodać do koszyka",
    )
    quantity = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(MAX_ITEM_QUANTITY)],
        help_text=f"Liczba sztuk pozycji, najwyżej {MAX_ITEM_QUANTITY}",
    )
    engraving_text = models.CharField(
        max_length=ENGRAVING_MAX_LENGTH,
        blank=True,
        help_text=(
            "Treść grawerunku; przy parze trafia na oba egzemplarze, o ile "
            "drugi nie ma własnej. Puste oznacza wyrób bez grawerunku."
        ),
    )
    second_size = models.CharField(
        max_length=2,
        choices=RingSize.choices,
        blank=True,
        help_text=(
            "Rozmiar drugiego egzemplarza pary. Wypełniony zamienia pozycję "
            "w parę; pierwszy rozmiar bierze się z wariantu."
        ),
    )
    second_engraving_text = models.CharField(
        max_length=ENGRAVING_MAX_LENGTH,
        blank=True,
        help_text="Grawerunek drugiego egzemplarza, gdy ma być inny niż pierwszego",
    )

    class Meta:
        verbose_name = "Pozycja koszyka"
        verbose_name_plural = "Pozycje koszyka"
        ordering = ["created_at", "id"]
        constraints = [
            # Pozycje różniące się wyłącznie ilością mają być jedną pozycją —
            # scala je serwis dodawania. Pozycje różniące się personalizacją
            # są osobne i to ograniczenie ich nie dotyczy.
            models.UniqueConstraint(
                fields=[
                    "cart",
                    "variant",
                    "engraving_text",
                    "second_size",
                    "second_engraving_text",
                ],
                name="cart_item_unique_per_personalisation",
            ),
            models.CheckConstraint(
                condition=models.Q(quantity__gte=1)
                & models.Q(quantity__lte=MAX_ITEM_QUANTITY),
                name="cart_item_quantity_within_limit",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.variant.sku} × {self.quantity}"

    @property
    def is_pair(self) -> bool:
        """Para poznaje się po drugim rozmiarze — innego znacznika nie ma."""
        return bool(self.second_size)

    @property
    def specimen_count(self) -> int:
        """Ile sztuk wyrobu kryje jedna sztuka pozycji: para to dwie."""
        return 2 if self.is_pair else 1

    @property
    def unit_price(self) -> Money:
        """Cena jednego egzemplarza — aktualna, prosto z wariantu."""
        return self.variant.effective_price

    @property
    def goods_price(self) -> Money:
        """Wartość samego towaru w pozycji, bez grawerunku."""
        return self.unit_price * (self.specimen_count * self.quantity)

    @property
    def engraving_price(self) -> Money:
        """Wartość grawerunku w pozycji, liczona za każdy grawerowany egzemplarz.

        Wspólna treść na parze nie jest tańsza od dwóch różnych: grawer to
        robota przy każdej obrączce z osobna, a nie przy zamówieniu.
        """
        price = self.variant.product.engraving_price_money
        if price is None or not self.engraving_text:
            return Money.zero(self.unit_price.currency)
        return price * (self.specimen_count * self.quantity)

    @property
    def line_total(self) -> Money:
        return self.goods_price + self.engraving_price

    def clean(self) -> None:
        super().clean()
        self._reject_invalid_personalisation()

    def save(self, *args, **kwargs) -> None:
        self._reject_invalid_personalisation()
        super().save(*args, **kwargs)

    def _reject_invalid_personalisation(self) -> None:
        product = self.variant.product

        if self.engraving_text and not product.is_engravable:
            raise ValidationError(
                {"engraving_text": "Tego wyrobu nie da się grawerować (ADR 0018)."}
            )
        if self.second_size and not product.is_made_to_order:
            raise ValidationError(
                {
                    "second_size": (
                        "Parę składa się wyłącznie z wyrobu na zamówienie "
                        "(ADR 0024). Wyrób magazynowy w drugim rozmiarze to "
                        "inny wariant, więc i osobna pozycja."
                    )
                }
            )
        if self.second_size and not self.variant.size:
            raise ValidationError(
                {
                    "second_size": (
                        "Parę można złożyć tylko z wyrobu, który ma rozmiar — "
                        "drugi egzemplarz nie miałby czym się różnić."
                    )
                }
            )
        if self.second_engraving_text and not self.is_pair:
            raise ValidationError(
                {
                    "second_engraving_text": (
                        "Osobny grawerunek ma sens dopiero przy drugim "
                        "egzemplarzu pary."
                    )
                }
            )
        if self.second_engraving_text and not self.engraving_text:
            raise ValidationError(
                {
                    "engraving_text": (
                        "Drugi egzemplarz ma grawerunek, a pierwszy nie — "
                        "podaj oba albo żaden."
                    )
                }
            )
