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
class TestTokenGoscia:
    def test_pierwsze_dodanie_zaklada_koszyk_z_tokenem(self):
        cart = get_or_create_cart(user=None, token=None)

        assert cart.is_guest is True
        assert cart.session_key != ""

    def test_kolejne_zadanie_z_tokenem_trafia_w_ten_sam_koszyk(self):
        first = get_or_create_cart(user=None, token=None)

        second = get_or_create_cart(user=None, token=first.session_key)

        assert second.pk == first.pk

    def test_nieznany_token_dostaje_nowy_koszyk_zamiast_bledu(self):
        """Koszyk mógł wygasnąć albo zostać scalony — klient zaczyna od nowa."""
        cart = get_or_create_cart(user=None, token="token-ktorego-nie-ma")

        assert cart.session_key != "token-ktorego-nie-ma"

    def test_zalogowany_dostaje_koszyk_konta_mimo_tokenu(self):
        user = UserFactory()
        guest = GuestCartFactory()

        cart = get_or_create_cart(user=user, token=guest.session_key)

        assert cart.user_id == user.pk  # type: ignore[missing-attribute]
        assert cart.session_key == ""

    def test_brak_koszyka_to_brak_wyniku_a_nie_nowy_wiersz(self):
        assert get_cart(user=None, token=None) is None
        assert Cart.objects.count() == 0


@pytest.mark.django_db
class TestDodawaniePozycji:
    def test_ta_sama_personalizacja_dolicza_sztuki(self):
        cart = CartFactory()
        variant = _variant()
        stock(variant, 10)

        add_item(cart, variant=variant, quantity=1)
        item = add_item(cart, variant=variant, quantity=2)

        assert cart.items.count() == 1
        assert item.quantity == 3

    def test_inny_grawer_zaklada_osobna_pozycje(self):
        cart = CartFactory()
        product = EngravableProductFactory(engraving_price=4900)
        variant = ProductVariantFactory(product=product)
        stock(variant, 10)

        add_item(cart, variant=variant, quantity=1, engraving_text="Ania")
        add_item(cart, variant=variant, quantity=1, engraving_text="Jan")

        assert cart.items.count() == 2

    def test_ponad_pieciu_sztuk_nie_da_sie_dodac(self):
        cart = CartFactory()
        variant = _variant()
        stock(variant, 100)

        with pytest.raises(ValidationError) as error:
            add_item(cart, variant=variant, quantity=MAX_ITEM_QUANTITY + 1)

        assert "quantity" in error.value.message_dict

    def test_limit_obowiazuje_takze_przy_dokladaniu(self):
        cart = CartFactory()
        variant = _variant()
        stock(variant, 100)
        add_item(cart, variant=variant, quantity=4)

        with pytest.raises(ValidationError):
            add_item(cart, variant=variant, quantity=2)

    def test_ilosc_ponad_stan_jest_odrzucona(self):
        cart = CartFactory()
        variant = _variant()
        stock(variant, 2)

        with pytest.raises(ValidationError) as error:
            add_item(cart, variant=variant, quantity=3)

        assert "quantity" in error.value.message_dict

    def test_produkt_na_zamowienie_omija_stan(self):
        cart = CartFactory()
        variant = ProductVariantFactory(product=MadeToOrderProductFactory())

        item = add_item(cart, variant=variant, quantity=MAX_ITEM_QUANTITY)

        assert item.quantity == MAX_ITEM_QUANTITY

    def test_grawer_na_produkcie_bez_grawerunku_jest_odrzucony(self):
        cart = CartFactory()
        variant = _variant()
        stock(variant, 10)

        with pytest.raises(ValidationError) as error:
            add_item(cart, variant=variant, quantity=1, engraving_text="Ania")

        assert "engraving_text" in error.value.message_dict


@pytest.mark.django_db
class TestZmianaIlosci:
    def test_zero_usuwa_pozycje(self):
        item = CartItemFactory(quantity=2)
        stock(item.variant, 10)

        set_quantity(item, 0)

        assert CartItem.objects.filter(pk=item.pk).exists() is False

    def test_ponad_stan_jest_odrzucone(self):
        item = CartItemFactory(quantity=1)
        stock(item.variant, 2)

        with pytest.raises(ValidationError):
            set_quantity(item, 3)


@pytest.mark.django_db
class TestScalanie:
    def test_pozycje_goscia_trafiaja_do_koszyka_konta(self):
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

    def test_koszyk_goscia_znika_razem_z_tokenem(self):
        guest = GuestCartFactory()
        token = guest.session_key
        target = CartFactory()

        merge_carts(guest=guest, target=target)

        assert get_cart(user=None, token=token) is None

    def test_ta_sama_pozycja_sumuje_ilosci(self):
        guest = GuestCartFactory()
        target = CartFactory()
        variant = _variant()
        stock(variant, 10)
        CartItemFactory(cart=guest, variant=variant, quantity=2)
        CartItemFactory(cart=target, variant=variant, quantity=1)

        merged = merge_carts(guest=guest, target=target)

        assert merged.items.get().quantity == 3

    def test_scalanie_nie_omija_limitu_sztuk(self):
        guest = GuestCartFactory()
        target = CartFactory()
        variant = _variant()
        stock(variant, 100)
        CartItemFactory(cart=guest, variant=variant, quantity=4)
        CartItemFactory(cart=target, variant=variant, quantity=4)

        merged = merge_carts(guest=guest, target=target)

        assert merged.items.get().quantity == MAX_ITEM_QUANTITY

    def test_scalanie_przycina_ilosc_do_stanu(self):
        """Koszyk gościa mógł leżeć tygodniami — jego ilości wymagają sprawdzenia na nowo."""
        guest = GuestCartFactory()
        target = CartFactory()
        variant = _variant()
        stock(variant, 2)
        CartItemFactory(cart=guest, variant=variant, quantity=2)
        CartItemFactory(cart=target, variant=variant, quantity=2)

        merged = merge_carts(guest=guest, target=target)

        assert merged.items.get().quantity == 2

    def test_pozycja_przenoszona_tez_jest_sprawdzana_wzgledem_stanu(self):
        guest = GuestCartFactory()
        target = CartFactory()
        variant = _variant()
        stock(variant, 1)
        CartItemFactory(cart=guest, variant=variant, quantity=4)

        merged = merge_carts(guest=guest, target=target)

        assert merged.items.get().quantity == 1

    def test_pozycja_bez_stanu_zostaje_widoczna_zamiast_zniknac(self):
        guest = GuestCartFactory()
        target = CartFactory()
        variant = _variant()
        stock(variant, 0)
        CartItemFactory(cart=guest, variant=variant, quantity=3)

        merged = merge_carts(guest=guest, target=target)

        assert merged.items.get().quantity == 1

    def test_rozny_grawer_zostaje_osobna_pozycja(self):
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
class TestPodsumowanie:
    def test_suma_liczy_towar_i_grawerunek(self):
        cart = CartFactory()
        product = EngravableProductFactory(engraving_price=4900)
        variant = ProductVariantFactory(product=product, price=100000)
        stock(variant, 10)
        add_item(cart, variant=variant, quantity=2, engraving_text="Ania")

        summary = totals(cart_items(cart))

        assert summary.item_count == 1
        assert summary.subtotal == Money(209800)
        assert summary.total == Money(209800)

    def test_rabat_i_kupon_sa_na_razie_zerowe(self):
        cart = CartFactory()
        variant = _variant(price=100000)
        stock(variant, 10)
        add_item(cart, variant=variant, quantity=1)

        summary = totals(cart_items(cart))

        assert summary.discount_amount == Money(0)
        assert summary.coupon_amount == Money(0)

    def test_pusty_koszyk_ma_zerowa_sume(self):
        summary = totals(cart_items(CartFactory()))

        assert summary.item_count == 0
        assert summary.total == Money(0)

    def test_para_liczy_sie_jako_jedna_pozycja_i_dwa_egzemplarze(self):
        cart = CartFactory()
        variant = ProductVariantFactory(
            product=MadeToOrderProductFactory(), price=100000, size=RingSize.S16
        )

        add_item(cart, variant=variant, quantity=1, second_size=RingSize.S20)

        summary = totals(cart_items(cart))
        assert summary.item_count == 1
        assert summary.total == Money(200000)
