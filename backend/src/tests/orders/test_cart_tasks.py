"""Sprzątanie koszyków gości zadaniem okresowym (ADR 0030)."""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.orders.models import GUEST_CART_TTL_DAYS, Cart
from apps.orders.tasks import purge_stale_guest_carts
from tests.factories.orders import CartFactory, GuestCartFactory


def _inactive_for(cart: Cart, days: int) -> Cart:
    Cart.objects.filter(pk=cart.pk).update(
        last_activity_at=timezone.now() - timedelta(days=days)
    )
    return cart


@pytest.mark.django_db
class TestGuestCartCleanup:
    """Sprzątanie porzuconych koszyków gości."""

    def test_guest_cart_disappears_after_thirty_days(self):
        """Koszyk gościa po trzydziestu dniach znika."""
        stale = _inactive_for(GuestCartFactory(), GUEST_CART_TTL_DAYS + 1)

        deleted = purge_stale_guest_carts()  # type: ignore[missing-argument]

        assert deleted == 1
        assert Cart.objects.filter(pk=stale.pk).exists() is False

    def test_fresh_guest_cart_stays(self):
        """Świeży koszyk gościa zostaje."""
        fresh = _inactive_for(GuestCartFactory(), GUEST_CART_TTL_DAYS - 1)

        purge_stale_guest_carts()  # type: ignore[missing-argument]

        assert Cart.objects.filter(pk=fresh.pk).exists() is True

    def test_viewed_guest_cart_is_not_abandoned(self):
        """Odczyt też jest aktywnością — inaczej klient traci koszyk, z którego korzysta."""
        cart = _inactive_for(GuestCartFactory(), GUEST_CART_TTL_DAYS - 1)

        cart.refresh_from_db()
        cart.touch_on_read()
        purge_stale_guest_carts()  # type: ignore[missing-argument]

        assert Cart.objects.filter(pk=cart.pk).exists() is True
        cart.refresh_from_db()
        assert timezone.now() - cart.last_activity_at < timedelta(minutes=1)

    def test_read_right_after_change_costs_no_write(self):
        """Odczyt tuż po zmianie nie kosztuje zapisu."""
        cart = GuestCartFactory()
        before = Cart.objects.get(pk=cart.pk).last_activity_at

        cart.touch_on_read()

        assert Cart.objects.get(pk=cart.pk).last_activity_at == before

    def test_account_cart_is_not_cleaned_up(self):
        """Koszyk konta nie jest sprzątany.

        Klient ma prawo wrócić po roku i zastać to, co zostawił.
        """
        owned = _inactive_for(CartFactory(), GUEST_CART_TTL_DAYS * 12)

        purge_stale_guest_carts()  # type: ignore[missing-argument]

        assert Cart.objects.filter(pk=owned.pk).exists() is True
