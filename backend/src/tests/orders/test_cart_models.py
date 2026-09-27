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
class TestWlascicielKoszyka:
    """Koszyk należy do konta albo do gościa — nigdy do obu (ADR 0030)."""

    def test_koszyk_z_kontem_i_tokenem_jest_odrzucony(self):
        with pytest.raises(ValidationError) as error:
            CartFactory(session_key="token-gosca")

        assert "session_key" in error.value.message_dict

    def test_koszyk_bez_konta_i_bez_tokenu_jest_odrzucony(self):
        with pytest.raises(ValidationError):
            Cart(user=None, session_key="").save()

    def test_ograniczenie_w_bazie_lapie_zapis_z_pominieciem_walidacji(self):
        cart = GuestCartFactory()

        with pytest.raises(IntegrityError):
            Cart.objects.filter(pk=cart.pk).update(session_key="")

    def test_token_gosca_jest_niepowtarzalny(self):
        first = GuestCartFactory()

        with pytest.raises(IntegrityError):
            GuestCartFactory(session_key=first.session_key)

    def test_konto_ma_najwyzej_jeden_koszyk(self):
        cart = CartFactory()

        with pytest.raises(IntegrityError):
            CartFactory(user=cart.user)


@pytest.mark.django_db
class TestWycenaPozycji:
    """Koszyk pokazuje cenę aktualną, nie zamrożoną (`CONTEXT.md`, CartItem)."""

    def test_cena_pozycji_idzie_za_zmiana_ceny_wariantu(self):
        variant = ProductVariantFactory(price=100000)
        item = CartItemFactory(variant=variant, quantity=2)

        variant.price = 150000
        variant.save()
        item.refresh_from_db()

        assert item.goods_price == Money(300000)

    def test_cena_reczna_ma_pierwszenstwo(self):
        variant = ProductVariantFactory(price=100000, manual_price=79900)
        item = CartItemFactory(variant=variant, quantity=1)

        assert item.goods_price == Money(79900)

    def test_grawerunek_jest_wyceniony_osobno(self):
        product = EngravableProductFactory(engraving_price=4900)
        variant = ProductVariantFactory(product=product, price=100000)

        item = CartItemFactory(variant=variant, quantity=2, engraving_text="Ania")

        assert item.goods_price == Money(200000)
        assert item.engraving_price == Money(9800)
        assert item.line_total == Money(209800)

    def test_bez_grawerunku_cena_grawerunku_jest_zerowa(self):
        product = EngravableProductFactory(engraving_price=4900)
        variant = ProductVariantFactory(product=product, price=100000)

        item = CartItemFactory(variant=variant, engraving_text="")

        assert item.engraving_price == Money(0)


@pytest.mark.django_db
class TestPara:
    """Para obrączek to jedna pozycja z dwoma egzemplarzami (ADR 0024)."""

    def test_para_kosztuje_podwojnie(self):
        variant = _wedding_band(price=100000)

        item = CartItemFactory(variant=variant, second_size=RingSize.S20)

        assert item.is_pair is True
        assert item.specimen_count == 2
        assert item.goods_price == Money(200000)

    def test_wspolny_grawer_jest_naliczony_za_kazdy_egzemplarz(self):
        variant = _wedding_band(price=100000, engraving_price=4900)

        item = CartItemFactory(
            variant=variant, second_size=RingSize.S20, engraving_text="2026-06-13"
        )

        assert item.engraving_price == Money(9800)

    def test_osobny_grawer_kosztuje_tyle_samo_co_wspolny(self):
        variant = _wedding_band(price=100000, engraving_price=4900)

        item = CartItemFactory(
            variant=variant,
            second_size=RingSize.S20,
            engraving_text="Ania",
            second_engraving_text="Jan",
        )

        assert item.engraving_price == Money(9800)

    def test_drugi_rozmiar_wymaga_wariantu_z_rozmiarem(self):
        variant = ProductVariantFactory(
            product=MadeToOrderProductFactory(), size="", length=""
        )

        with pytest.raises(ValidationError) as error:
            CartItemFactory(variant=variant, second_size=RingSize.S20)

        assert "second_size" in error.value.message_dict

    def test_wyrob_magazynowy_nie_daje_sie_zlozyc_w_pare(self):
        """Drugi rozmiar wyrobu ze stanem to inny wariant, nie drugi egzemplarz."""
        variant = ProductVariantFactory(size=RingSize.S16)

        with pytest.raises(ValidationError) as error:
            CartItemFactory(variant=variant, second_size=RingSize.S20)

        assert "second_size" in error.value.message_dict

    def test_osobny_grawer_bez_pary_jest_odrzucony(self):
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
class TestWalidacjaGrawerunku:
    def test_grawer_na_produkcie_bez_grawerunku_jest_odrzucony(self):
        variant = ProductVariantFactory()

        with pytest.raises(ValidationError) as error:
            CartItemFactory(variant=variant, engraving_text="Ania")

        assert "engraving_text" in error.value.message_dict


@pytest.mark.django_db
class TestPozycjeSieNieScalaja:
    def test_ta_sama_pozycja_dwa_razy_lamie_ograniczenie(self):
        cart = CartFactory()
        variant = ProductVariantFactory()
        CartItemFactory(cart=cart, variant=variant)

        with pytest.raises(IntegrityError):
            CartItem.objects.create(cart=cart, variant=variant, quantity=1)

    def test_ten_sam_wariant_z_roznym_grawerem_to_dwie_pozycje(self):
        cart = CartFactory()
        product = EngravableProductFactory(engraving_price=4900)
        variant = ProductVariantFactory(product=product)

        CartItemFactory(cart=cart, variant=variant, engraving_text="Ania")
        CartItemFactory(cart=cart, variant=variant, engraving_text="Jan")

        assert cart.items.count() == 2
