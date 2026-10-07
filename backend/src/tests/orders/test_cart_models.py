"""Reguły koszyka pilnowane przez model (`CONTEXT.md`, Cart/CartItem)."""

from __future__ import annotations

import pytest
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

from apps.orders.models import Cart, CartItem
from apps.products.models import RingSize
from common.money import Money
from tests.factories.orders import CartFactory, CartItemFactory, GuestCartFactory
from tests.factories.products import (
    EngravableProductFactory,
    MadeToOrderProductFactory,
    ProductVariantFactory,
)


def _wedding_band(*, price: int, engraving_price: int | None = None):
    """Obrączka: wyrób na zamówienie z rozmiarem, czyli jedyny kandydat na parę."""
    product = MadeToOrderProductFactory(
        is_engravable=engraving_price is not None,
        engraving_price=engraving_price,
    )
    return ProductVariantFactory(product=product, price=price, size=RingSize.S16)


@pytest.mark.django_db
class TestCartOwner:
    """Koszyk należy do konta albo do gościa — nigdy do obu (ADR 0030)."""

    def test_cart_with_account_and_token_is_rejected(self):
        """Koszyk z kontem i tokenem naraz jest odrzucany."""
        with pytest.raises(ValidationError) as error:
            CartFactory(session_key="token-gosca")

        assert "session_key" in error.value.message_dict

    def test_cart_without_account_and_token_is_rejected(self):
        """Koszyk bez konta i bez tokenu jest odrzucany."""
        with pytest.raises(ValidationError):
            Cart(user=None, session_key="").save()

    def test_database_constraint_catches_unvalidated_save(self):
        """Ograniczenie w bazie łapie zapis z pominięciem walidacji."""
        cart = GuestCartFactory()

        with pytest.raises(IntegrityError):
            Cart.objects.filter(pk=cart.pk).update(session_key="")

    def test_guest_token_is_unique(self):
        """Token gościa jest niepowtarzalny."""
        first = GuestCartFactory()

        with pytest.raises(IntegrityError):
            GuestCartFactory(session_key=first.session_key)

    def test_account_has_at_most_one_cart(self):
        """Konto ma najwyżej jeden koszyk."""
        cart = CartFactory()

        with pytest.raises(IntegrityError):
            CartFactory(user=cart.user)


@pytest.mark.django_db
class TestItemPricing:
    """Koszyk pokazuje cenę aktualną, nie zamrożoną (`CONTEXT.md`, CartItem)."""

    def test_item_price_follows_variant_price_change(self):
        """Cena pozycji idzie za zmianą ceny wariantu."""
        variant = ProductVariantFactory(price=100000)
        item = CartItemFactory(variant=variant, quantity=2)

        variant.price = 150000
        variant.save()
        item.refresh_from_db()

        assert item.goods_price == Money(300000)

    def test_manual_price_takes_precedence(self):
        """Cena ręczna ma pierwszeństwo."""
        variant = ProductVariantFactory(price=100000, manual_price=79900)
        item = CartItemFactory(variant=variant, quantity=1)

        assert item.goods_price == Money(79900)

    def test_engraving_is_priced_separately(self):
        """Grawerunek jest wyceniony osobno."""
        product = EngravableProductFactory(engraving_price=4900)
        variant = ProductVariantFactory(product=product, price=100000)

        item = CartItemFactory(variant=variant, quantity=2, engraving_text="Ania")

        assert item.goods_price == Money(200000)
        assert item.engraving_price == Money(9800)
        assert item.line_total == Money(209800)

    def test_without_engraving_engraving_price_is_zero(self):
        """Bez grawerunku cena grawerunku jest zerowa."""
        product = EngravableProductFactory(engraving_price=4900)
        variant = ProductVariantFactory(product=product, price=100000)

        item = CartItemFactory(variant=variant, engraving_text="")

        assert item.engraving_price == Money(0)


@pytest.mark.django_db
class TestPair:
    """Para obrączek to jedna pozycja z dwoma egzemplarzami (ADR 0024)."""

    def test_pair_costs_double(self):
        """Para kosztuje podwójnie."""
        variant = _wedding_band(price=100000)

        item = CartItemFactory(variant=variant, second_size=RingSize.S20)

        assert item.is_pair is True
        assert item.specimen_count == 2
        assert item.goods_price == Money(200000)

    def test_shared_engraving_is_charged_per_specimen(self):
        """Wspólny grawer jest naliczany za każdy egzemplarz."""
        variant = _wedding_band(price=100000, engraving_price=4900)

        item = CartItemFactory(
            variant=variant, second_size=RingSize.S20, engraving_text="2026-06-13"
        )

        assert item.engraving_price == Money(9800)

    def test_separate_engraving_costs_same_as_shared(self):
        """Osobny grawer kosztuje tyle samo co wspólny."""
        variant = _wedding_band(price=100000, engraving_price=4900)

        item = CartItemFactory(
            variant=variant,
            second_size=RingSize.S20,
            engraving_text="Ania",
            second_engraving_text="Jan",
        )

        assert item.engraving_price == Money(9800)

    def test_second_size_requires_sized_variant(self):
        """Drugi rozmiar wymaga wariantu z rozmiarem."""
        variant = ProductVariantFactory(
            product=MadeToOrderProductFactory(), size="", length=""
        )

        with pytest.raises(ValidationError) as error:
            CartItemFactory(variant=variant, second_size=RingSize.S20)

        assert "second_size" in error.value.message_dict

    def test_stocked_product_cannot_form_pair(self):
        """Drugi rozmiar wyrobu ze stanem to inny wariant, nie drugi egzemplarz."""
        variant = ProductVariantFactory(size=RingSize.S16)

        with pytest.raises(ValidationError) as error:
            CartItemFactory(variant=variant, second_size=RingSize.S20)

        assert "second_size" in error.value.message_dict

    def test_separate_engraving_without_pair_is_rejected(self):
        """Osobny grawer bez pary jest odrzucany."""
        product = EngravableProductFactory(engraving_price=4900)
        variant = ProductVariantFactory(product=product, size=RingSize.S16)

        with pytest.raises(ValidationError) as error:
            CartItemFactory(
                variant=variant,
                engraving_text="Ania",
                second_engraving_text="Jan",
            )

        assert "second_engraving_text" in error.value.message_dict


@pytest.mark.django_db
class TestEngravingValidation:
    """Walidacja grawerunku w koszyku."""

    def test_engraving_on_non_engravable_product_is_rejected(self):
        """Grawer na produkcie bez grawerunku jest odrzucany."""
        variant = ProductVariantFactory()

        with pytest.raises(ValidationError) as error:
            CartItemFactory(variant=variant, engraving_text="Ania")

        assert "engraving_text" in error.value.message_dict


@pytest.mark.django_db
class TestItemsAreNotMerged:
    """Pozycje koszyka się nie scalają."""

    def test_same_item_twice_breaks_constraint(self):
        """Ta sama pozycja dwa razy łamie ograniczenie bazy."""
        cart = CartFactory()
        variant = ProductVariantFactory()
        CartItemFactory(cart=cart, variant=variant)

        with pytest.raises(IntegrityError):
            CartItem.objects.create(cart=cart, variant=variant, quantity=1)

    def test_same_variant_with_different_engraving_is_two_items(self):
        """Ten sam wariant z różnym grawerem to dwie pozycje."""
        cart = CartFactory()
        product = EngravableProductFactory(engraving_price=4900)
        variant = ProductVariantFactory(product=product)

        CartItemFactory(cart=cart, variant=variant, engraving_text="Ania")
        CartItemFactory(cart=cart, variant=variant, engraving_text="Jan")

        assert cart.items.count() == 2


@pytest.mark.django_db
class TestCartReminderMoment:
    """Moment przypomnienia (`CONTEXT.md`, CartReminder, #208)."""

    def test_content_change_clears_reminder_moment(self):
        """Zmiana zawartości koszyka zeruje moment przypomnienia."""
        from django.utils import timezone

        cart = CartFactory(reminded_at=timezone.now())

        cart.touch()

        cart.refresh_from_db()
        assert cart.reminded_at is None

    def test_reading_cart_keeps_reminder_moment(self):
        """Odczyt koszyka nie rusza momentu przypomnienia."""
        from datetime import timedelta

        from django.utils import timezone

        reminded = timezone.now()
        cart = CartFactory(
            reminded_at=reminded, last_activity_at=reminded - timedelta(days=2)
        )

        cart.touch_on_read()

        cart.refresh_from_db()
        assert cart.reminded_at == reminded
        assert timezone.now() - cart.last_activity_at < timedelta(minutes=1)
