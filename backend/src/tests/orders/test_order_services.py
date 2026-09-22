"""Składanie zamówienia z koszyka (`CONTEXT.md`, Order; ADR 0010, 0030)."""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.consents.models import ConsentKind
from apps.inventory.models import ReservationStatus
from apps.orders.models import (
    GUEST_ORDER_LIMIT,
    UNPAID_ORDER_TTL,
    Order,
    OrderStatus,
)
from apps.orders.services import (
    OrderError,
    ShippingAddress,
    attach_guest_orders,
    cancel_order,
    create_order,
    expire_unpaid_orders,
    resolve_zone,
)
from apps.orders.services.cart import add_item
from apps.shipping.models import ShippingZone
from common.money import Money
from tests.factories.accounts import UserFactory
from tests.factories.consents import (
    ConsentDocumentFactory,
    ConsentFactory,
    GuestConsentFactory,
)
from tests.factories.orders import CartFactory, GuestCartFactory
from tests.factories.products import (
    EngravableProductFactory,
    MadeToOrderProductFactory,
    ProductVariantFactory,
    PublishedProductFactory,
    stock,
)
from tests.factories.shipping import ShippingMethodFactory

ADDRESS = ShippingAddress(
    recipient_name="Jan Kowalski",
    street="Złota 44",
    city="Warszawa",
    postal_code="00-120",
    country="PL",
)


def _variant(**kwargs):
    kwargs.setdefault("product", PublishedProductFactory())
    return ProductVariantFactory(**kwargs)


def _terms_for(user=None, email: str = ""):
    """Bieżący regulamin plus zgoda podmiotu — bez niej zamówienie nie powstanie."""
    document = ConsentDocumentFactory(kind=ConsentKind.TERMS)
    if user is not None:
        ConsentFactory(user=user, document=document)
    else:
        GuestConsentFactory(email=email, document=document)
    return document


@pytest.mark.django_db
class TestStrefaDostawy:
    def test_polska_to_strefa_krajowa(self):
        assert resolve_zone("PL") == ShippingZone.PL

    def test_kraj_unii_to_strefa_unijna(self):
        assert resolve_zone("DE") == ShippingZone.EU

    def test_kraj_spoza_unii_jest_odrzucony(self):
        with pytest.raises(OrderError) as error:
            resolve_zone("US")

        assert "country" in error.value.message_dict


@pytest.mark.django_db
class TestSkladanieZamowienia:
    def test_zamowienie_powstaje_w_statusie_pending(self, settings):
        settings.FREE_SHIPPING_THRESHOLD = None
        user = UserFactory()
        _terms_for(user=user)
        cart = CartFactory(user=user)
        variant = _variant(price=100000)
        stock(variant, 5)
        add_item(cart, variant=variant, quantity=2)

        order = create_order(
            cart=cart,
            address=ADDRESS,
            shipping_method=ShippingMethodFactory(rate=1990),
            user=user,
        )

        assert order.status == OrderStatus.PENDING
        assert order.email == user.email
        assert order.total == Money(201990)

    def test_darmowa_dostawa_powyzej_progu_zamraza_zero(self, settings):
        """Koszt dostawy jest kopiowany taki, jaki klient widział w kasie."""
        settings.FREE_SHIPPING_THRESHOLD = 50000
        user = UserFactory()
        _terms_for(user=user)
        cart = CartFactory(user=user)
        variant = _variant(price=100000)
        stock(variant, 5)
        add_item(cart, variant=variant, quantity=1)

        order = create_order(
            cart=cart,
            address=ADDRESS,
            shipping_method=ShippingMethodFactory(rate=1990),
            user=user,
        )

        assert order.shipping_cost == 0
        assert order.total == Money(100000)

    def test_koszyk_jest_czyszczony(self):
        user = UserFactory()
        _terms_for(user=user)
        cart = CartFactory(user=user)
        variant = _variant()
        stock(variant, 5)
        add_item(cart, variant=variant, quantity=1)

        create_order(
            cart=cart,
            address=ADDRESS,
            shipping_method=ShippingMethodFactory(),
            user=user,
        )

        assert cart.items.count() == 0

    def test_rezerwacje_powstaja_i_obnizaja_dostepnosc(self):
        user = UserFactory()
        _terms_for(user=user)
        cart = CartFactory(user=user)
        variant = _variant()
        stock(variant, 5)
        add_item(cart, variant=variant, quantity=2)

        order = create_order(
            cart=cart,
            address=ADDRESS,
            shipping_method=ShippingMethodFactory(),
            user=user,
        )

        assert order.reservations.count() == 1  # type: ignore[missing-attribute]
        variant.refresh_from_db()
        assert variant.available == 3

    def test_wyrob_na_zamowienie_nie_dostaje_rezerwacji(self):
        user = UserFactory()
        _terms_for(user=user)
        cart = CartFactory(user=user)
        variant = ProductVariantFactory(product=MadeToOrderProductFactory())
        add_item(cart, variant=variant, quantity=1)

        order = create_order(
            cart=cart,
            address=ADDRESS,
            shipping_method=ShippingMethodFactory(),
            user=user,
        )

        assert order.reservations.count() == 0  # type: ignore[missing-attribute]
        assert order.has_made_to_order_item is True

    def test_pusty_koszyk_jest_odrzucony(self):
        user = UserFactory()
        _terms_for(user=user)

        with pytest.raises(OrderError) as error:
            create_order(
                cart=CartFactory(user=user),
                address=ADDRESS,
                shipping_method=ShippingMethodFactory(),
                user=user,
            )

        assert "cart" in error.value.message_dict


@pytest.mark.django_db
class TestSnapshot:
    """Pozycja zamówienia trzyma kopię, nie odwołanie (ADR 0010)."""

    def test_cena_przezywa_zmiane_cennika(self):
        user = UserFactory()
        _terms_for(user=user)
        cart = CartFactory(user=user)
        variant = _variant(price=100000)
        stock(variant, 5)
        add_item(cart, variant=variant, quantity=1)
        order = create_order(
            cart=cart,
            address=ADDRESS,
            shipping_method=ShippingMethodFactory(rate=0),
            user=user,
        )

        variant.price = 250000
        variant.save()

        order.refresh_from_db()
        assert order.items.get().unit_price == 100000
        assert order.total == Money(100000)

    def test_nazwa_i_sku_sa_skopiowane(self):
        user = UserFactory()
        _terms_for(user=user)
        cart = CartFactory(user=user)
        product = PublishedProductFactory(name="Pierścionek Bella")
        variant = ProductVariantFactory(product=product, sku="RING-001")
        stock(variant, 5)
        add_item(cart, variant=variant, quantity=1)

        order = create_order(
            cart=cart,
            address=ADDRESS,
            shipping_method=ShippingMethodFactory(),
            user=user,
        )

        item = order.items.get()
        assert item.product_name == "Pierścionek Bella"
        assert item.sku == "RING-001"

    def test_grawerunek_i_jego_cena_sa_skopiowane(self):
        user = UserFactory()
        _terms_for(user=user)
        cart = CartFactory(user=user)
        product = EngravableProductFactory(engraving_price=4900)
        variant = ProductVariantFactory(product=product, price=100000)
        stock(variant, 5)
        add_item(cart, variant=variant, quantity=1, engraving_text="Ania")

        order = create_order(
            cart=cart,
            address=ADDRESS,
            shipping_method=ShippingMethodFactory(rate=0),
            user=user,
        )

        item = order.items.get()
        assert item.engraving_text == "Ania"
        assert item.engraving_total == Money(4900)
        assert order.total == Money(104900)

    def test_koszt_dostawy_jest_zamrozony(self):
        user = UserFactory()
        _terms_for(user=user)
        cart = CartFactory(user=user)
        variant = _variant(price=10000)
        stock(variant, 5)
        add_item(cart, variant=variant, quantity=1)
        method = ShippingMethodFactory(rate=1990)
        order = create_order(
            cart=cart, address=ADDRESS, shipping_method=method, user=user
        )

        method.rate = 4990
        method.save()

        order.refresh_from_db()
        assert order.shipping_cost == 1990


@pytest.mark.django_db
class TestWalidacje:
    def test_bez_zgody_na_regulamin_zamowienie_nie_powstaje(self):
        user = UserFactory()
        ConsentDocumentFactory(kind=ConsentKind.TERMS)
        cart = CartFactory(user=user)
        variant = _variant()
        stock(variant, 5)
        add_item(cart, variant=variant, quantity=1)

        with pytest.raises(OrderError) as error:
            create_order(
                cart=cart,
                address=ADDRESS,
                shipping_method=ShippingMethodFactory(),
                user=user,
            )

        assert "terms" in error.value.message_dict

    def test_nowa_wersja_regulaminu_uniewaznia_stara_zgode(self):
        user = UserFactory()
        _terms_for(user=user)
        ConsentDocumentFactory(
            kind=ConsentKind.TERMS,
            version="nowsza",
            effective_from=timezone.localdate(),
        )
        cart = CartFactory(user=user)
        variant = _variant()
        stock(variant, 5)
        add_item(cart, variant=variant, quantity=1)

        with pytest.raises(OrderError) as error:
            create_order(
                cart=cart,
                address=ADDRESS,
                shipping_method=ShippingMethodFactory(),
                user=user,
            )

        assert "terms" in error.value.message_dict

    def test_gosc_powyzej_progu_wymaga_konta(self):
        email = "gosc@test.com"
        _terms_for(email=email)
        cart = GuestCartFactory()
        variant = _variant(price=GUEST_ORDER_LIMIT + 1)
        stock(variant, 5)
        add_item(cart, variant=variant, quantity=1)

        with pytest.raises(OrderError) as error:
            create_order(
                cart=cart,
                address=ADDRESS,
                shipping_method=ShippingMethodFactory(),
                email=email,
            )

        assert "email" in error.value.message_dict

    def test_zalogowany_nie_ma_progu(self):
        user = UserFactory()
        _terms_for(user=user)
        cart = CartFactory(user=user)
        variant = _variant(price=GUEST_ORDER_LIMIT + 1)
        stock(variant, 5)
        add_item(cart, variant=variant, quantity=1)

        order = create_order(
            cart=cart,
            address=ADDRESS,
            shipping_method=ShippingMethodFactory(),
            user=user,
        )

        assert order.status == OrderStatus.PENDING

    def test_metoda_ponad_swoj_limit_jest_odrzucona(self):
        user = UserFactory()
        _terms_for(user=user)
        cart = CartFactory(user=user)
        variant = _variant(price=600000)
        stock(variant, 5)
        add_item(cart, variant=variant, quantity=1)

        with pytest.raises(OrderError) as error:
            create_order(
                cart=cart,
                address=ADDRESS,
                shipping_method=ShippingMethodFactory(max_order_value=500000),
                user=user,
            )

        assert "shipping_method" in error.value.message_dict

    def test_metoda_z_innej_strefy_jest_odrzucona(self):
        user = UserFactory()
        _terms_for(user=user)
        cart = CartFactory(user=user)
        variant = _variant()
        stock(variant, 5)
        add_item(cart, variant=variant, quantity=1)

        with pytest.raises(OrderError) as error:
            create_order(
                cart=cart,
                address=ADDRESS,
                shipping_method=ShippingMethodFactory(zone=ShippingZone.EU),
                user=user,
            )

        assert "shipping_method" in error.value.message_dict

    def test_ilosc_ponad_stan_zatrzymuje_zamowienie(self):
        user = UserFactory()
        _terms_for(user=user)
        cart = CartFactory(user=user)
        variant = _variant()
        item_stock = stock(variant, 5)
        add_item(cart, variant=variant, quantity=3)
        # Stan schodzi po włożeniu do koszyka — klient dowiaduje się przy kasie.
        item_stock.movements.create(quantity=-4, reason="loss")

        with pytest.raises(OrderError) as error:
            create_order(
                cart=cart,
                address=ADDRESS,
                shipping_method=ShippingMethodFactory(),
                user=user,
            )

        assert "items" in error.value.message_dict

    def test_nieudane_zamowienie_nie_czysci_koszyka(self):
        user = UserFactory()
        ConsentDocumentFactory(kind=ConsentKind.TERMS)
        cart = CartFactory(user=user)
        variant = _variant()
        stock(variant, 5)
        add_item(cart, variant=variant, quantity=1)

        with pytest.raises(OrderError):
            create_order(
                cart=cart,
                address=ADDRESS,
                shipping_method=ShippingMethodFactory(),
                user=user,
            )

        assert cart.items.count() == 1
        assert Order.objects.count() == 0


@pytest.mark.django_db
class TestPrzejsciaStatusow:
    def _order(self, **kwargs) -> Order:
        user = UserFactory()
        _terms_for(user=user)
        cart = CartFactory(user=user)
        product = (
            MadeToOrderProductFactory()
            if kwargs.pop("made_to_order", False)
            else PublishedProductFactory()
        )
        variant = ProductVariantFactory(product=product)
        if not product.is_made_to_order:
            stock(variant, 5)
        add_item(cart, variant=variant, quantity=1)
        return create_order(
            cart=cart,
            address=ADDRESS,
            shipping_method=ShippingMethodFactory(),
            user=user,
        )

    def test_pending_przechodzi_w_paid(self):
        order = self._order()

        order.transition_to(OrderStatus.PAID)

        assert order.status == OrderStatus.PAID

    def test_przejscie_wstecz_jest_odrzucone(self):
        order = self._order()
        order.transition_to(OrderStatus.PAID)

        with pytest.raises(ValidationError):
            order.transition_to(OrderStatus.PENDING)

    def test_produkcja_wymaga_wyrobu_na_zamowienie(self):
        order = self._order()
        order.transition_to(OrderStatus.PAID)

        with pytest.raises(ValidationError):
            order.transition_to(OrderStatus.IN_PRODUCTION)

    def test_produkcja_przy_wyrobie_na_zamowienie_przechodzi(self):
        order = self._order(made_to_order=True)
        order.transition_to(OrderStatus.PAID)

        order.transition_to(OrderStatus.IN_PRODUCTION)

        assert order.status == OrderStatus.IN_PRODUCTION

    def test_anulowane_jest_stanem_koncowym(self):
        order = self._order()
        order.transition_to(OrderStatus.CANCELLED)

        with pytest.raises(ValidationError):
            order.transition_to(OrderStatus.PAID)

    def test_wyslane_idzie_tylko_do_dostarczonego(self):
        order = self._order()
        order.transition_to(OrderStatus.PAID)
        order.transition_to(OrderStatus.PACKED)
        order.transition_to(OrderStatus.SHIPPED)

        with pytest.raises(ValidationError):
            order.transition_to(OrderStatus.CANCELLED)

        order.transition_to(OrderStatus.DELIVERED)
        assert order.status == OrderStatus.DELIVERED


@pytest.mark.django_db
class TestAnulowanie:
    def _pending_order(self):
        user = UserFactory()
        _terms_for(user=user)
        cart = CartFactory(user=user)
        variant = _variant()
        stock(variant, 5)
        add_item(cart, variant=variant, quantity=2)
        order = create_order(
            cart=cart,
            address=ADDRESS,
            shipping_method=ShippingMethodFactory(),
            user=user,
        )
        return order, variant

    def test_anulowanie_zwalnia_rezerwacje(self):
        order, variant = self._pending_order()

        cancel_order(order)

        assert order.status == OrderStatus.CANCELLED
        assert (
            order.reservations.get().status  # type: ignore[missing-attribute]
            == ReservationStatus.RELEASED
        )
        variant.refresh_from_db()
        assert variant.available == 5

    def test_anulowanie_oplaconego_jest_odrzucone(self):
        order, _ = self._pending_order()
        order.transition_to(OrderStatus.PAID)

        with pytest.raises(OrderError) as error:
            cancel_order(order)

        assert "status" in error.value.message_dict


@pytest.mark.django_db
class TestZadanieSprzatajace:
    def test_nieoplacone_po_dobie_jest_anulowane(self):
        user = UserFactory()
        _terms_for(user=user)
        cart = CartFactory(user=user)
        variant = _variant()
        stock(variant, 5)
        add_item(cart, variant=variant, quantity=1)
        order = create_order(
            cart=cart,
            address=ADDRESS,
            shipping_method=ShippingMethodFactory(),
            user=user,
        )
        Order.objects.filter(pk=order.pk).update(
            created_at=timezone.now() - UNPAID_ORDER_TTL - timedelta(minutes=1)
        )

        assert expire_unpaid_orders(older_than=timezone.now() - UNPAID_ORDER_TTL) == 1

        order.refresh_from_db()
        assert order.status == OrderStatus.CANCELLED

    def test_swieze_zamowienie_zostaje(self):
        user = UserFactory()
        _terms_for(user=user)
        cart = CartFactory(user=user)
        variant = _variant()
        stock(variant, 5)
        add_item(cart, variant=variant, quantity=1)
        order = create_order(
            cart=cart,
            address=ADDRESS,
            shipping_method=ShippingMethodFactory(),
            user=user,
        )

        expire_unpaid_orders(older_than=timezone.now() - UNPAID_ORDER_TTL)

        order.refresh_from_db()
        assert order.status == OrderStatus.PENDING


@pytest.mark.django_db
class TestZamowieniaGoscia:
    def test_zamowienie_goscia_trafia_do_konta_na_ten_sam_adres(self):
        email = "gosc@test.com"
        _terms_for(email=email)
        cart = GuestCartFactory()
        variant = _variant()
        stock(variant, 5)
        add_item(cart, variant=variant, quantity=1)
        order = create_order(
            cart=cart,
            address=ADDRESS,
            shipping_method=ShippingMethodFactory(),
            email=email,
        )

        user = UserFactory(email=email)

        order.refresh_from_db()
        assert order.user_id == user.pk  # type: ignore[missing-attribute]

    def test_cudze_zamowienie_nie_trafia_do_konta(self):
        email = "gosc@test.com"
        _terms_for(email=email)
        cart = GuestCartFactory()
        variant = _variant()
        stock(variant, 5)
        add_item(cart, variant=variant, quantity=1)
        order = create_order(
            cart=cart,
            address=ADDRESS,
            shipping_method=ShippingMethodFactory(),
            email=email,
        )

        other = UserFactory(email="ktos.inny@test.com")
        attach_guest_orders(other)

        order.refresh_from_db()
        assert order.user_id is None  # type: ignore[missing-attribute]
