"""Kupon jako forma zapłaty za towar po promocjach (ADR 0011, 0014, 0023)."""

from __future__ import annotations

from datetime import timedelta
from typing import Any
from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.throttling import SimpleRateThrottle

from apps.consents.models import ConsentDocument, ConsentKind
from apps.inventory.models import ReservationStatus
from apps.orders.models import OrderStatus
from apps.orders.services import (
    CartError,
    OrderError,
    ShippingAddress,
    add_item,
    apply_coupon_code,
    cancel_order,
    cart_items,
    create_order,
    merge_carts,
    promotions_for,
    totals,
)
from apps.payments.models import Payment
from apps.products.services.metal_rate import activate_rate
from apps.promotions.models import CouponRedemption, CouponStatus
from apps.promotions.tasks import expire_coupons
from common.money import Money
from tests.factories.accounts import UserFactory
from tests.factories.consents import ConsentDocumentFactory, ConsentFactory
from tests.factories.orders import CartFactory, GuestCartFactory
from tests.factories.products import (
    MetalRateFactory,
    ProductVariantFactory,
    PublishedProductFactory,
    stock,
)
from tests.factories.promotions import CouponFactory, PromotionFactory
from tests.factories.shipping import ShippingMethodFactory

ADDRESS = ShippingAddress(
    recipient_name="Jan Kowalski",
    street="Złota 44",
    city="Warszawa",
    postal_code="00-120",
    country="PL",
)


@pytest.fixture(autouse=True)
def _no_free_shipping(settings):
    settings.FREE_SHIPPING_THRESHOLD = None


@pytest.fixture(autouse=True)
def _active_rate():
    activate_rate(MetalRateFactory(price_per_gram=10000))


@pytest.fixture(autouse=True)
def terms():
    return ConsentDocumentFactory(kind=ConsentKind.TERMS)


def _cart_with_variant(cart, *, price: int = 100000):
    variant = ProductVariantFactory(product=PublishedProductFactory(), price=price)
    stock(variant, 5)
    add_item(cart, variant=variant)
    return variant


def _user_with_terms():
    user = UserFactory()
    ConsentFactory(
        user=user, document=ConsentDocument.objects.current(ConsentKind.TERMS)
    )
    return user


def _order(cart, user, *, shipping_rate: int = 1990):
    return create_order(
        cart=cart,
        address=ADDRESS,
        shipping_method=ShippingMethodFactory(rate=shipping_rate),
        user=user,
    )


def _cart_totals(cart):
    items = list(cart_items(cart))
    return totals(items, promotions_for(cart, items), coupon=cart.coupon)


@pytest.mark.django_db
class TestCouponModel:
    @pytest.mark.parametrize("nominal", [9500, 0, -1000])
    def test_nominal_not_multiple_of_ten_zloty_is_rejected(self, nominal):
        """95 zł, zero i kwota ujemna nie przechodzą ani walidacji, ani zapisu."""
        with pytest.raises(ValidationError):
            CouponFactory.build(nominal=nominal).full_clean()
        with pytest.raises(ValidationError):
            CouponFactory(nominal=nominal)

    def test_any_multiple_of_ten_zloty_is_accepted(self):
        """Kupon ze zwrotu zaokrąglony w górę do pełnych 10 zł, np. 70 zł."""
        CouponFactory.build(nominal=7000).full_clean()

    def test_valid_for_twelve_months_with_shop_code(self):
        """Nowy kupon: ważny 12 miesięcy, kod nadany przez sklep, status `issued`."""
        coupon = CouponFactory()

        assert coupon.status == CouponStatus.ISSUED
        assert coupon.code
        assert (
            timedelta(days=364)
            < coupon.expires_at - timezone.now()
            <= timedelta(days=366)
        )

    def test_expire_task_marks_overdue_coupons(self):
        """Zadanie okresowe zamyka kupony po terminie, ważnych nie rusza."""
        overdue = CouponFactory(expires_at=timezone.now() - timedelta(days=1))
        valid = CouponFactory()

        assert expire_coupons() == 1  # type: ignore[missing-argument]

        overdue.refresh_from_db()
        valid.refresh_from_db()
        assert overdue.status == CouponStatus.EXPIRED
        assert valid.status == CouponStatus.ISSUED


@pytest.mark.django_db
class TestApplyCoupon:
    def test_unknown_code_is_rejected(self):
        with pytest.raises(CartError):
            apply_coupon_code(CartFactory(), "NIEMA")

    def test_expired_coupon_is_rejected(self):
        """Kupon po terminie nie wchodzi do koszyka, choć status jeszcze `issued`."""
        coupon = CouponFactory(expires_at=timezone.now() - timedelta(minutes=1))

        with pytest.raises(CartError):
            apply_coupon_code(CartFactory(), coupon.code)

    def test_redeemed_coupon_is_rejected(self):
        coupon = CouponFactory(status=CouponStatus.REDEEMED)

        with pytest.raises(CartError):
            apply_coupon_code(CartFactory(), coupon.code)

    def test_coupon_counts_after_promotions(self):
        """1000 zł − 10% promocji = 900 zł; kupon 100 zł zostawia 800 zł."""
        cart = CartFactory()
        _cart_with_variant(cart)
        PromotionFactory(value=10)
        apply_coupon_code(cart, CouponFactory().code.lower())

        summary = _cart_totals(cart)

        assert summary.discount_amount == Money(10000)
        assert summary.coupon_amount == Money(10000)
        assert summary.total == Money(80000)

    def test_coupon_above_goods_is_capped(self):
        """Kupon 500 zł na towar za 300 zł pokrywa 300 zł — reszta przepada."""
        cart = CartFactory()
        _cart_with_variant(cart, price=30000)
        apply_coupon_code(cart, CouponFactory(nominal=50000).code)

        summary = _cart_totals(cart)

        assert summary.coupon_amount == Money(30000)
        assert summary.total == Money(0)

    def test_guest_coupon_replaces_dead_account_coupon(self):
        """Konto ma kupon już wykorzystany — przejmuje działający kupon gościa."""
        coupon = CouponFactory()
        guest = GuestCartFactory()
        apply_coupon_code(guest, coupon.code)
        target = CartFactory(coupon=CouponFactory(status=CouponStatus.REDEEMED))

        merged = merge_carts(guest=guest, target=target)

        merged.refresh_from_db()
        assert merged.coupon == coupon

    def test_guest_coupon_survives_login(self):
        """Kupon wpisany jako gość przechodzi do koszyka konta przy scaleniu."""
        coupon = CouponFactory()
        guest = GuestCartFactory()
        apply_coupon_code(guest, coupon.code)

        merged = merge_carts(guest=guest, target=CartFactory())

        merged.refresh_from_db()
        assert merged.coupon == coupon


@pytest.mark.django_db
class TestOrderWithCoupon:
    def test_coupon_never_covers_shipping(self):
        """Kupon 500 zł na towar za 300 zł: do zapłaty zostaje sama dostawa."""
        user = _user_with_terms()
        cart = CartFactory(user=user)
        _cart_with_variant(cart, price=30000)
        coupon = CouponFactory(nominal=50000)
        apply_coupon_code(cart, coupon.code)

        order = _order(cart, user)

        assert order.coupon_amount == 30000
        assert order.total == Money(1990)
        assert order.status == OrderStatus.PENDING

    def test_redemption_recorded_and_coupon_used_once(self):
        """Zamówienie zapisuje faktycznie naliczoną kwotę; kupon staje się `redeemed`."""
        user = _user_with_terms()
        cart = CartFactory(user=user)
        _cart_with_variant(cart)
        coupon = CouponFactory()
        apply_coupon_code(cart, coupon.code)

        order = _order(cart, user)

        coupon.refresh_from_db()
        cart.refresh_from_db()
        redemption = CouponRedemption.objects.get(order=order)
        assert redemption.coupon == coupon
        assert redemption.amount == 10000
        assert coupon.status == CouponStatus.REDEEMED
        assert cart.coupon is None
        with pytest.raises(CartError):
            apply_coupon_code(CartFactory(), coupon.code)

    def test_coupon_redeemed_elsewhere_rejects_the_order(self):
        """Ten sam kod w dwóch koszykach: drugie zamówienie odmówione, nie droższe.

        Klient widział w koszyku sumę po kuponie — cicha zmiana kwoty przy
        składaniu byłaby gorsza niż jawna odmowa.
        """
        coupon = CouponFactory()
        first_user, second_user = _user_with_terms(), _user_with_terms()
        first_cart, second_cart = (
            CartFactory(user=first_user),
            CartFactory(user=second_user),
        )
        for cart in (first_cart, second_cart):
            _cart_with_variant(cart)
            apply_coupon_code(cart, coupon.code)

        first = _order(first_cart, first_user)
        with pytest.raises(OrderError) as error:
            _order(second_cart, second_user)

        assert first.coupon_amount == 10000
        assert "coupon" in error.value.message_dict
        assert CouponRedemption.objects.filter(coupon=coupon).count() == 1

    def test_full_coverage_with_free_shipping_is_paid_without_intent(self):
        """Towar pokryty kuponem i darmowa dostawa: `paid` bez operatora płatności."""
        user = _user_with_terms()
        cart = CartFactory(user=user)
        _cart_with_variant(cart, price=30000)
        apply_coupon_code(cart, CouponFactory(nominal=50000).code)

        order = _order(cart, user, shipping_rate=0)

        assert order.total == Money(0)
        assert order.status == OrderStatus.PAID
        assert not Payment.objects.filter(order=order).exists()
        assert {r.status for r in order.reservations.all()} == {  # type: ignore[missing-attribute]
            ReservationStatus.CONSUMED
        }

    def test_order_paid_with_coupon_can_be_cancelled(self, api_client: APIClient):
        """Opłacone w całości kuponem: anulowanie od razu, towar i kupon wracają."""
        user = _user_with_terms()
        cart = CartFactory(user=user)
        variant = _cart_with_variant(cart, price=30000)
        coupon = CouponFactory(nominal=50000)
        apply_coupon_code(cart, coupon.code)
        order = _order(cart, user, shipping_rate=0)
        api_client.force_authenticate(user)

        response: Any = api_client.post(reverse("order-cancel", args=[order.number]))

        order.refresh_from_db()
        coupon.refresh_from_db()
        assert response.status_code == status.HTTP_200_OK
        assert order.status == OrderStatus.CANCELLED
        assert coupon.status == CouponStatus.ISSUED
        assert type(variant).objects.get(pk=variant.pk).available == 5

    def test_cancelled_unpaid_order_gives_coupon_back(self):
        """Klient nic nie kupił — kupon wraca do użycia."""
        user = _user_with_terms()
        cart = CartFactory(user=user)
        _cart_with_variant(cart)
        coupon = CouponFactory()
        apply_coupon_code(cart, coupon.code)
        order = _order(cart, user)

        cancel_order(order)

        coupon.refresh_from_db()
        assert coupon.status == CouponStatus.ISSUED


@pytest.mark.django_db
class TestCartCouponView:
    def _guest_cart_token(self, client: APIClient) -> str:
        variant = ProductVariantFactory(product=PublishedProductFactory(), price=100000)
        stock(variant, 5)
        response: Any = client.post(
            reverse("cart-item-list"), {"variant": str(variant.pk), "quantity": 1}
        )
        return response.json()["cartToken"]

    def test_coupon_lowers_cart_total(self, api_client: APIClient):
        token = self._guest_cart_token(api_client)
        coupon = CouponFactory()

        response: Any = api_client.post(
            reverse("cart-coupon"), {"code": coupon.code}, HTTP_X_CART_TOKEN=token
        )

        body = response.json()
        assert response.status_code == status.HTTP_200_OK
        assert body["couponCode"] == coupon.code
        assert body["couponAmount"] == {"amount": 10000, "currency": "PLN"}
        assert body["total"] == {"amount": 90000, "currency": "PLN"}

    def test_unknown_code_is_400(self, api_client: APIClient):
        token = self._guest_cart_token(api_client)

        response: Any = api_client.post(
            reverse("cart-coupon"), {"code": "NIEMA"}, HTTP_X_CART_TOKEN=token
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "code" in response.json()

    def test_guessing_codes_is_throttled(self, api_client: APIClient):
        """Zgadywanie kodów hamuje zakres `auth`."""
        with patch.dict(SimpleRateThrottle.THROTTLE_RATES, {"auth": "1/min"}):
            api_client.post(reverse("cart-coupon"), {"code": "NIEMA1"})
            response: Any = api_client.post(reverse("cart-coupon"), {"code": "NIEMA2"})

        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    @pytest.mark.parametrize(
        "coupon_kwargs",
        [
            {"status": CouponStatus.REDEEMED},
            {"expires_at": timezone.now() - timedelta(minutes=1)},
        ],
    )
    def test_used_or_expired_code_is_400(self, api_client: APIClient, coupon_kwargs):
        token = self._guest_cart_token(api_client)
        coupon = CouponFactory(**coupon_kwargs)

        response: Any = api_client.post(
            reverse("cart-coupon"), {"code": coupon.code}, HTTP_X_CART_TOKEN=token
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "code" in response.json()

    def test_delete_removes_coupon(self, api_client: APIClient):
        token = self._guest_cart_token(api_client)
        coupon = CouponFactory()
        api_client.post(
            reverse("cart-coupon"), {"code": coupon.code}, HTTP_X_CART_TOKEN=token
        )

        response: Any = api_client.delete(
            reverse("cart-coupon"), HTTP_X_CART_TOKEN=token
        )

        body = response.json()
        assert response.status_code == status.HTTP_200_OK
        assert body["couponCode"] is None
        assert body["couponAmount"]["amount"] == 0
        assert body["total"]["amount"] == 100000

    def test_dead_coupon_is_not_shown(self, api_client: APIClient):
        """Kupon wykorzystany w innym zamówieniu znika z podglądu koszyka."""
        token = self._guest_cart_token(api_client)
        coupon = CouponFactory()
        api_client.post(
            reverse("cart-coupon"), {"code": coupon.code}, HTTP_X_CART_TOKEN=token
        )
        coupon.status = CouponStatus.REDEEMED
        coupon.save()

        body = api_client.get(reverse("cart-detail"), HTTP_X_CART_TOKEN=token).json()  # type: ignore[attr-defined]

        assert body["couponCode"] is None
        assert body["couponAmount"]["amount"] == 0
