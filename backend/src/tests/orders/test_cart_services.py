"""Serwis koszyka: token gościa, scalanie, limity (ADR 0030)."""

from __future__ import annotations

import pytest
from django.core.exceptions import ValidationError

from apps.orders.models import MAX_ITEM_QUANTITY, Cart, CartItem
from apps.orders.services import (
    add_item,
    get_cart,
    get_or_create_cart,
    cart_items,
    merge_carts,
    set_quantity,
    totals,
)
from apps.products.models import RingSize
from common.money import Money
from tests.factories.accounts import UserFactory
from tests.factories.orders import CartFactory, CartItemFactory, GuestCartFactory
from tests.factories.products import (
    EngravableProductFactory,
    MadeToOrderProductFactory,
    ProductVariantFactory,
    PublishedProductFactory,
    stock,
)


def _variant(**kwargs):
    """Wariant, który klient może kupić — produkt opublikowany, nie szkic."""
    kwargs.setdefault("product", PublishedProductFactory())
    return ProductVariantFactory(**kwargs)


@pytest.mark.django_db
class TestGuestToken:
    """Token gościa wskazuje jego koszyk."""

    def test_first_add_creates_cart_with_token(self):
        """Pierwsze dodanie zakłada koszyk z tokenem."""
        cart = get_or_create_cart(user=None, token=None)

        assert cart.is_guest is True
        assert cart.session_key != ""

    def test_next_request_with_token_hits_same_cart(self):
        """Kolejne żądanie z tokenem trafia w ten sam koszyk."""
        first = get_or_create_cart(user=None, token=None)

        second = get_or_create_cart(user=None, token=first.session_key)

        assert second.pk == first.pk

    def test_unknown_token_gets_new_cart_instead_of_error(self):
        """Koszyk mógł wygasnąć albo zostać scalony — klient zaczyna od nowa."""
        cart = get_or_create_cart(user=None, token="token-ktorego-nie-ma")

        assert cart.session_key != "token-ktorego-nie-ma"

    def test_logged_in_gets_account_cart_despite_token(self):
        """Zalogowany dostaje koszyk konta mimo tokenu."""
        user = UserFactory()
        guest = GuestCartFactory()

        cart = get_or_create_cart(user=user, token=guest.session_key)

        assert cart.user_id == user.pk  # type: ignore[missing-attribute]
        assert cart.session_key == ""

    def test_missing_cart_returns_none_instead_of_new_row(self):
        """Brak koszyka to brak wyniku, a nie nowy wiersz."""
        assert get_cart(user=None, token=None) is None
        assert Cart.objects.count() == 0


@pytest.mark.django_db
class TestAddingItems:
    """Dodawanie pozycji do koszyka."""

    def test_same_personalisation_adds_quantity(self):
        """Ta sama personalizacja dolicza sztuki."""
        cart = CartFactory()
        variant = _variant()
        stock(variant, 10)

        add_item(cart, variant=variant, quantity=1)
        item = add_item(cart, variant=variant, quantity=2)

        assert cart.items.count() == 1
        assert item.quantity == 3

    def test_other_engraving_creates_separate_item(self):
        """Inny grawer zakłada osobną pozycję."""
        cart = CartFactory()
        product = EngravableProductFactory(engraving_price=4900)
        variant = ProductVariantFactory(product=product)
        stock(variant, 10)

        add_item(cart, variant=variant, quantity=1, engraving_text="Ania")
        add_item(cart, variant=variant, quantity=1, engraving_text="Jan")

        assert cart.items.count() == 2

    def test_cannot_add_more_than_five(self):
        """Ponad pięciu sztuk nie da się dodać."""
        cart = CartFactory()
        variant = _variant()
        stock(variant, 100)

        with pytest.raises(ValidationError) as error:
            add_item(cart, variant=variant, quantity=MAX_ITEM_QUANTITY + 1)

        assert "quantity" in error.value.message_dict

    def test_limit_applies_when_adding_more(self):
        """Limit obowiązuje także przy dokładaniu."""
        cart = CartFactory()
        variant = _variant()
        stock(variant, 100)
        add_item(cart, variant=variant, quantity=4)

        with pytest.raises(ValidationError):
            add_item(cart, variant=variant, quantity=2)

    def test_quantity_above_stock_is_rejected(self):
        """Ilość ponad stan jest odrzucana."""
        cart = CartFactory()
        variant = _variant()
        stock(variant, 2)

        with pytest.raises(ValidationError) as error:
            add_item(cart, variant=variant, quantity=3)

        assert "quantity" in error.value.message_dict

    def test_made_to_order_product_skips_stock(self):
        """Produkt na zamówienie omija stan."""
        cart = CartFactory()
        variant = ProductVariantFactory(product=MadeToOrderProductFactory())

        item = add_item(cart, variant=variant, quantity=MAX_ITEM_QUANTITY)

        assert item.quantity == MAX_ITEM_QUANTITY

    def test_engraving_on_non_engravable_product_is_rejected(self):
        """Grawer na produkcie bez grawerunku jest odrzucany."""
        cart = CartFactory()
        variant = _variant()
        stock(variant, 10)

        with pytest.raises(ValidationError) as error:
            add_item(cart, variant=variant, quantity=1, engraving_text="Ania")

        assert "engraving_text" in error.value.message_dict


@pytest.mark.django_db
class TestQuantityChange:
    """Zmiana ilości pozycji."""

    def test_zero_removes_item(self):
        """Zero usuwa pozycję."""
        item = CartItemFactory(quantity=2)
        stock(item.variant, 10)

        set_quantity(item, 0)

        assert CartItem.objects.filter(pk=item.pk).exists() is False

    def test_above_stock_is_rejected(self):
        """Ilość ponad stan jest odrzucana."""
        item = CartItemFactory(quantity=1)
        stock(item.variant, 2)

        with pytest.raises(ValidationError):
            set_quantity(item, 3)


@pytest.mark.django_db
class TestMerge:
    """Scalanie koszyka gościa z koszykiem konta."""

    def test_guest_items_go_to_account_cart(self):
        """Pozycje gościa trafiają do koszyka konta."""
        guest = GuestCartFactory()
        target = CartFactory()
        variant = _variant()
        stock(variant, 10)
        CartItemFactory(cart=guest, variant=variant, quantity=2)

        merged = merge_carts(guest=guest, target=target)

        assert merged.pk == target.pk
        assert [item.variant_id for item in merged.items.all()] == [  # type: ignore[missing-attribute]
            variant.pk
        ]

    def test_guest_cart_disappears_with_token(self):
        """Koszyk gościa znika razem z tokenem."""
        guest = GuestCartFactory()
        token = guest.session_key
        target = CartFactory()

        merge_carts(guest=guest, target=target)

        assert get_cart(user=None, token=token) is None

    def test_same_item_sums_quantities(self):
        """Ta sama pozycja sumuje ilości."""
        guest = GuestCartFactory()
        target = CartFactory()
        variant = _variant()
        stock(variant, 10)
        CartItemFactory(cart=guest, variant=variant, quantity=2)
        CartItemFactory(cart=target, variant=variant, quantity=1)

        merged = merge_carts(guest=guest, target=target)

        assert merged.items.get().quantity == 3

    def test_merge_respects_quantity_limit(self):
        """Scalanie nie omija limitu sztuk."""
        guest = GuestCartFactory()
        target = CartFactory()
        variant = _variant()
        stock(variant, 100)
        CartItemFactory(cart=guest, variant=variant, quantity=4)
        CartItemFactory(cart=target, variant=variant, quantity=4)

        merged = merge_carts(guest=guest, target=target)

        assert merged.items.get().quantity == MAX_ITEM_QUANTITY

    def test_merge_caps_quantity_at_stock(self):
        """Koszyk gościa mógł leżeć tygodniami — jego ilości wymagają sprawdzenia na nowo."""
        guest = GuestCartFactory()
        target = CartFactory()
        variant = _variant()
        stock(variant, 2)
        CartItemFactory(cart=guest, variant=variant, quantity=2)
        CartItemFactory(cart=target, variant=variant, quantity=2)

        merged = merge_carts(guest=guest, target=target)

        assert merged.items.get().quantity == 2

    def test_moved_item_is_checked_against_stock(self):
        """Przenoszona pozycja też jest sprawdzana względem stanu."""
        guest = GuestCartFactory()
        target = CartFactory()
        variant = _variant()
        stock(variant, 1)
        CartItemFactory(cart=guest, variant=variant, quantity=4)

        merged = merge_carts(guest=guest, target=target)

        assert merged.items.get().quantity == 1

    def test_item_without_stock_stays_visible(self):
        """Pozycja bez stanu zostaje widoczna zamiast zniknąć."""
        guest = GuestCartFactory()
        target = CartFactory()
        variant = _variant()
        stock(variant, 0)
        CartItemFactory(cart=guest, variant=variant, quantity=3)

        merged = merge_carts(guest=guest, target=target)

        assert merged.items.get().quantity == 1

    def test_different_engraving_stays_separate_item(self):
        """Różny grawer zostaje osobną pozycją."""
        guest = GuestCartFactory()
        target = CartFactory()
        product = EngravableProductFactory(engraving_price=4900)
        variant = ProductVariantFactory(product=product)
        stock(variant, 10)
        CartItemFactory(cart=guest, variant=variant, engraving_text="Ania")
        CartItemFactory(cart=target, variant=variant, engraving_text="Jan")

        merged = merge_carts(guest=guest, target=target)

        assert merged.items.count() == 2


@pytest.mark.django_db
class TestSummary:
    """Podsumowanie koszyka."""

    def test_total_counts_goods_and_engraving(self):
        """Suma liczy towar i grawerunek."""
        cart = CartFactory()
        product = EngravableProductFactory(engraving_price=4900)
        variant = ProductVariantFactory(product=product, price=100000)
        stock(variant, 10)
        add_item(cart, variant=variant, quantity=2, engraving_text="Ania")

        summary = totals(cart_items(cart))

        assert summary.item_count == 1
        assert summary.subtotal == Money(209800)
        assert summary.total == Money(209800)

    def test_discount_and_coupon_are_zero_by_default(self):
        """Rabat i kupon są domyślnie zerowe."""
        cart = CartFactory()
        variant = _variant(price=100000)
        stock(variant, 10)
        add_item(cart, variant=variant, quantity=1)

        summary = totals(cart_items(cart))

        assert summary.discount_amount == Money(0)
        assert summary.coupon_amount == Money(0)

    def test_empty_cart_has_zero_total(self):
        """Pusty koszyk ma zerową sumę."""
        summary = totals(cart_items(CartFactory()))

        assert summary.item_count == 0
        assert summary.total == Money(0)

    def test_pair_counts_as_one_item_and_two_specimens(self):
        """Para liczy się jako jedna pozycja i dwa egzemplarze."""
        cart = CartFactory()
        variant = ProductVariantFactory(
            product=MadeToOrderProductFactory(), price=100000, size=RingSize.S16
        )

        add_item(cart, variant=variant, quantity=1, second_size=RingSize.S20)

        summary = totals(cart_items(cart))
        assert summary.item_count == 1
        assert summary.total == Money(200000)
