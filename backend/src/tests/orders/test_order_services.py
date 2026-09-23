"""Składanie zamówienia z koszyka (`CONTEXT.md`, Order; ADR 0010, 0030)."""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

import pytest
from allauth.account.models import EmailAddress
from allauth.account.signals import email_confirmed
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
class TestCreateOrder:
    def test_order_is_created_as_pending(self, settings):
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

    def test_free_shipping_above_threshold_freezes_zero(self, settings):
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

    def test_cart_is_cleared(self):
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

    def test_reservations_are_created_and_reduce_availability(self):
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

    def test_made_to_order_item_gets_no_reservation(self):
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

    def test_empty_cart_is_rejected(self):
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

    def test_non_eu_country_is_rejected(self):
        user = UserFactory()
        _terms_for(user=user)
        cart = CartFactory(user=user)
        variant = _variant()
        stock(variant, 5)
        add_item(cart, variant=variant, quantity=1)

        with pytest.raises(OrderError) as error:
            create_order(
                cart=cart,
                address=replace(ADDRESS, country="US"),
                shipping_method=ShippingMethodFactory(),
                user=user,
            )

        assert "country" in error.value.message_dict


@pytest.mark.django_db
class TestSnapshot:
    """Pozycja zamówienia trzyma kopię, nie odwołanie (ADR 0010)."""

    def test_price_survives_price_list_change(self):
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

    def test_name_and_sku_are_copied(self):
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

    def test_engraving_and_its_price_are_copied(self):
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

    def test_shipping_cost_is_frozen(self):
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
class TestValidation:
    def test_no_terms_consent_blocks_order(self):
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

    def test_new_terms_version_invalidates_old_consent(self):
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

    def test_guest_above_limit_requires_account(self):
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

    def test_guest_limit_includes_shipping_cost(self, settings):
        """Próg dotyczy kwoty, którą gość zostawia w sklepie — z dostawą włącznie."""
        settings.FREE_SHIPPING_THRESHOLD = None
        email = "gosc@test.com"
        _terms_for(email=email)
        cart = GuestCartFactory()
        variant = _variant(price=GUEST_ORDER_LIMIT)
        stock(variant, 5)
        add_item(cart, variant=variant, quantity=1)

        with pytest.raises(OrderError) as error:
            create_order(
                cart=cart,
                address=ADDRESS,
                shipping_method=ShippingMethodFactory(rate=1990),
                email=email,
            )

        assert "email" in error.value.message_dict

    def test_guest_exactly_at_limit_passes(self, settings):
        settings.FREE_SHIPPING_THRESHOLD = None
        email = "gosc@test.com"
        _terms_for(email=email)
        cart = GuestCartFactory()
        variant = _variant(price=GUEST_ORDER_LIMIT - 1990)
        stock(variant, 5)
        add_item(cart, variant=variant, quantity=1)

        order = create_order(
            cart=cart,
            address=ADDRESS,
            shipping_method=ShippingMethodFactory(rate=1990),
            email=email,
        )

        assert order.total == Money(GUEST_ORDER_LIMIT)

    def test_logged_in_user_has_no_limit(self):
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

    def test_method_above_its_limit_is_rejected(self):
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

    def test_method_from_other_zone_is_rejected(self):
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

    def test_quantity_above_stock_blocks_order(self):
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

    def test_failed_order_keeps_cart(self):
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
class TestStatusTransitions:
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

    def test_pending_moves_to_paid(self):
        order = self._order()

        order.transition_to(OrderStatus.PAID)

        assert order.status == OrderStatus.PAID

    def test_backward_transition_is_rejected(self):
        order = self._order()
        order.transition_to(OrderStatus.PAID)

        with pytest.raises(ValidationError):
            order.transition_to(OrderStatus.PENDING)

    def test_production_requires_made_to_order_item(self):
        order = self._order()
        order.transition_to(OrderStatus.PAID)

        with pytest.raises(ValidationError):
            order.transition_to(OrderStatus.IN_PRODUCTION)

    def test_production_with_made_to_order_item_passes(self):
        order = self._order(made_to_order=True)
        order.transition_to(OrderStatus.PAID)

        order.transition_to(OrderStatus.IN_PRODUCTION)

        assert order.status == OrderStatus.IN_PRODUCTION

    def test_cancelled_is_final_state(self):
        order = self._order()
        order.transition_to(OrderStatus.CANCELLED)

        with pytest.raises(ValidationError):
            order.transition_to(OrderStatus.PAID)

    def test_shipped_moves_only_to_delivered(self):
        order = self._order()
        order.transition_to(OrderStatus.PAID)
        order.transition_to(OrderStatus.PACKED)
        order.transition_to(OrderStatus.SHIPPED)

        with pytest.raises(ValidationError):
            order.transition_to(OrderStatus.CANCELLED)

        order.transition_to(OrderStatus.DELIVERED)
        assert order.status == OrderStatus.DELIVERED


@pytest.mark.django_db
class TestCancelOrder:
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

    def test_cancel_releases_reservations(self):
        order, variant = self._pending_order()

        cancel_order(order)

        assert order.status == OrderStatus.CANCELLED
        assert (
            order.reservations.get().status  # type: ignore[missing-attribute]
            == ReservationStatus.RELEASED
        )
        variant.refresh_from_db()
        assert variant.available == 5

    def test_cancel_paid_order_is_rejected(self):
        order, _ = self._pending_order()
        order.transition_to(OrderStatus.PAID)

        with pytest.raises(OrderError) as error:
            cancel_order(order)

        assert "status" in error.value.message_dict


@pytest.mark.django_db
class TestExpireUnpaidOrders:
    def test_unpaid_after_one_day_is_cancelled(self):
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

    def test_fresh_order_stays(self):
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
class TestGuestOrders:
    def _guest_order(self, email: str):
        _terms_for(email=email)
        cart = GuestCartFactory()
        variant = _variant()
        stock(variant, 5)
        add_item(cart, variant=variant, quantity=1)
        return create_order(
            cart=cart,
            address=ADDRESS,
            shipping_method=ShippingMethodFactory(),
            email=email,
        )

    def test_signup_alone_does_not_attach_orders(self):
        """Wpisanie cudzego adresu w rejestracji nie otwiera jego historii zakupów."""
        email = "gosc@test.com"
        order = self._guest_order(email)

        UserFactory(email=email)

        order.refresh_from_db()
        assert order.user_id is None  # type: ignore[missing-attribute]

    def test_email_confirmation_attaches_orders(self):
        email = "gosc@test.com"
        order = self._guest_order(email)
        user = UserFactory(email=email)
        address = EmailAddress.objects.create(
            user=user, email=email, primary=True, verified=True
        )

        email_confirmed.send(sender=EmailAddress, request=None, email_address=address)

        order.refresh_from_db()
        assert order.user_id == user.pk  # type: ignore[missing-attribute]

    def test_confirming_other_email_does_not_attach(self):
        order = self._guest_order("gosc@test.com")
        other = UserFactory(email="ktos.inny@test.com")
        address = EmailAddress.objects.create(
            user=other, email=other.email, primary=True, verified=True
        )

        email_confirmed.send(sender=EmailAddress, request=None, email_address=address)

        order.refresh_from_db()
        assert order.user_id is None  # type: ignore[missing-attribute]

    def test_service_attaches_only_given_email(self):
        order = self._guest_order("gosc@test.com")
        other = UserFactory(email="ktos.inny@test.com")

        attach_guest_orders(other)

        order.refresh_from_db()
        assert order.user_id is None  # type: ignore[missing-attribute]
