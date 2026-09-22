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
class TestSprzataniaKoszykowGosci:
    def test_koszyk_goscia_po_trzydziestu_dniach_znika(self):
        stale = _inactive_for(GuestCartFactory(), GUEST_CART_TTL_DAYS + 1)

        deleted = purge_stale_guest_carts()  # type: ignore[missing-argument]

        assert deleted == 1
        assert Cart.objects.filter(pk=stale.pk).exists() is False

    def test_swiezy_koszyk_goscia_zostaje(self):
        fresh = _inactive_for(GuestCartFactory(), GUEST_CART_TTL_DAYS - 1)

        purge_stale_guest_carts()  # type: ignore[missing-argument]

        assert Cart.objects.filter(pk=fresh.pk).exists() is True

    def test_koszyk_konta_nie_jest_sprzatany(self):
        """Klient ma prawo wrócić po roku i zastać to, co zostawił."""
        owned = _inactive_for(CartFactory(), GUEST_CART_TTL_DAYS * 12)

        purge_stale_guest_carts()  # type: ignore[missing-argument]

        assert Cart.objects.filter(pk=owned.pk).exists() is True
