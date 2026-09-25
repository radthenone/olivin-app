"""Zamówienie do strefy EU: euro po kursie z chwili złożenia (ADR 0019)."""

from __future__ import annotations

from dataclasses import replace
from datetime import date
from decimal import Decimal

import pytest

from apps.orders.services import OrderError, ShippingAddress, create_order
from apps.orders.services.cart import add_item
from apps.payments.services import start_payment
from apps.products.models import ExchangeRate
from apps.shipping.models import ShippingZone
from tests.factories.accounts import UserFactory
from tests.factories.consents import ConsentDocumentFactory, ConsentFactory
from tests.factories.orders import CartFactory
from tests.factories.products import (
    EngravableProductFactory,
    ProductVariantFactory,
    stock,
)
from tests.factories.promotions import CouponFactory
from tests.factories.shipping import ShippingMethodFactory

BERLIN = ShippingAddress(
    recipient_name="Anna Schmidt",
    street="Unter den Linden 1",
    city="Berlin",
    postal_code="10117",
    country="DE",
)


def _cart_with_item(*, price: int = 10001, engraving: str = ""):
    user = UserFactory()
    ConsentFactory(user=user, document=ConsentDocumentFactory(kind="terms"))
    cart = CartFactory(user=user)
    variant = ProductVariantFactory(
        product=EngravableProductFactory(engraving_price=4900), price=price
    )
    stock(variant, 5)
    add_item(cart, variant=variant, quantity=2, engraving_text=engraving)
    return user, cart


def _euro(rate: str = "4.000000") -> ExchangeRate:
    return ExchangeRate.objects.create(
        currency="EUR", rate=Decimal(rate), effective_on=date(2026, 9, 1), source="test"
    )


def _eu_method():
    return ShippingMethodFactory(zone=ShippingZone.EU, rate=8001)


@pytest.mark.django_db
class TestEuOrder:
    def test_order_is_in_euro_with_rate_snapshot(self, settings):
        settings.FREE_SHIPPING_THRESHOLD = None
        _euro("4.000000")
        user, cart = _cart_with_item(engraving="A&J")

        order = create_order(
            cart=cart, address=BERLIN, shipping_method=_eu_method(), user=user
        )

        assert order.currency == "EUR"
        assert order.exchange_rate == Decimal("4.000000")
        item = order.items.get()
        # 100,01 zł / 4 = 25,0025 € → 25,50 €; grawer 49 zł / 4 = 12,25 € → 12,50 €.
        assert item.unit_price == 2550
        assert item.engraving_price == 1250
        # Dostawa 80,01 zł / 4 = 20,0025 € → 20,01 € (w górę do centa).
        assert order.shipping_cost == 2001
        assert order.total.currency == "EUR"
        assert order.total.amount == 2 * 2550 + 2 * 1250 + 2001

    def test_later_rate_change_does_not_touch_order(self, settings):
        settings.FREE_SHIPPING_THRESHOLD = None
        _euro("4.000000")
        user, cart = _cart_with_item()
        order = create_order(
            cart=cart, address=BERLIN, shipping_method=_eu_method(), user=user
        )
        total = order.total

        ExchangeRate.objects.create(
            currency="EUR",
            rate=Decimal("5.000000"),
            effective_on=date(2026, 10, 1),
            source="test",
        )
        order.refresh_from_db()

        assert order.exchange_rate == Decimal("4.000000")
        assert order.total == total

    def test_payment_intent_is_in_euro(self, settings, fake_payment_provider):
        settings.FREE_SHIPPING_THRESHOLD = None
        _euro()
        user, cart = _cart_with_item()
        order = create_order(
            cart=cart, address=BERLIN, shipping_method=_eu_method(), user=user
        )

        started = start_payment(order)

        assert started.payment.currency == "EUR"
        assert fake_payment_provider.intents[0]["currency"] == "EUR"
        assert fake_payment_provider.intents[0]["amount"] == order.total.amount

    def test_polish_order_stays_in_pln(self, settings):
        settings.FREE_SHIPPING_THRESHOLD = None
        _euro()
        user, cart = _cart_with_item()

        order = create_order(
            cart=cart,
            address=replace(BERLIN, country="PL", postal_code="00-120"),
            shipping_method=ShippingMethodFactory(),
            user=user,
        )

        assert order.currency == "PLN"
        assert order.exchange_rate == Decimal("1.000000")
        assert order.items.get().unit_price == 10001

    def test_eu_order_without_rate_is_rejected(self):
        user, cart = _cart_with_item()

        with pytest.raises(OrderError) as error:
            create_order(
                cart=cart, address=BERLIN, shipping_method=_eu_method(), user=user
            )

        assert "currency" in error.value.message_dict

    def test_pln_coupon_cannot_pay_euro_order(self):
        _euro()
        user, cart = _cart_with_item()
        cart.coupon = CouponFactory()
        cart.save()

        with pytest.raises(OrderError) as error:
            create_order(
                cart=cart, address=BERLIN, shipping_method=_eu_method(), user=user
            )

        assert "coupon" in error.value.message_dict
