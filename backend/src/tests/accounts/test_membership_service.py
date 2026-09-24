"""Nadanie premium po progu dostarczonych zamówień (`CONTEXT.md`, Membership; ADR 0023)."""

from __future__ import annotations

import pytest
from django.utils import timezone

from apps.accounts.models import MembershipLevel
from apps.accounts.services.membership_service import (
    grant_premium_if_eligible,
    is_premium,
    paid_total,
)
from apps.orders.models import OrderStatus
from common.money import Money
from tests.factories.accounts import ProfileFactory, UserFactory
from tests.factories.orders import OrderFactory, OrderItemFactory


@pytest.mark.django_db
class TestPaidTotal:
    """Suma dostarczonych zamówień: po rabatach, bez dostawy, bez zwróconych."""

    def test_sums_delivered_orders_after_discount(self):
        user = UserFactory()
        order = OrderFactory(
            user=user, status=OrderStatus.DELIVERED, discount_amount=10000
        )
        OrderItemFactory(order=order, unit_price=100000, quantity=1)

        assert paid_total(user) == Money(90000)

    def test_excludes_shipping_cost(self):
        user = UserFactory()
        order = OrderFactory(
            user=user,
            status=OrderStatus.DELIVERED,
            shipping_cost=5000,
            discount_amount=0,
        )
        OrderItemFactory(order=order, unit_price=100000, quantity=1)

        assert paid_total(user) == Money(100000)

    def test_excludes_returned_orders(self):
        user = UserFactory()
        returned = OrderFactory(user=user, status=OrderStatus.RETURNED)
        OrderItemFactory(order=returned, unit_price=100000, quantity=1)

        assert paid_total(user) == Money.zero()

    def test_excludes_orders_not_yet_delivered(self):
        user = UserFactory()
        pending = OrderFactory(user=user, status=OrderStatus.PAID)
        OrderItemFactory(order=pending, unit_price=100000, quantity=1)

        assert paid_total(user) == Money.zero()

    def test_excludes_orders_in_other_currencies(self):
        """Zamówienia w euro nie liczą się do progu, który jest w groszach PLN."""
        user = UserFactory()
        order = OrderFactory(user=user, status=OrderStatus.DELIVERED, currency="EUR")
        OrderItemFactory(order=order, unit_price=100000, quantity=1)

        assert paid_total(user) == Money.zero()

    def test_sums_across_several_delivered_orders(self):
        user = UserFactory()
        first = OrderFactory(user=user, status=OrderStatus.DELIVERED)
        OrderItemFactory(order=first, unit_price=50000, quantity=1)
        second = OrderFactory(user=user, status=OrderStatus.DELIVERED)
        OrderItemFactory(order=second, unit_price=70000, quantity=1)

        assert paid_total(user) == Money(120000)


@pytest.mark.django_db
class TestGrantPremiumIfEligible:
    """Premium nadawane bezterminowo po przekroczeniu progu; nigdy odbierane."""

    def test_grants_premium_above_threshold(self, settings):
        settings.PREMIUM_MEMBERSHIP_THRESHOLD = 50000
        user = UserFactory()
        profile = ProfileFactory(user=user)
        order = OrderFactory(user=user, status=OrderStatus.DELIVERED)
        OrderItemFactory(order=order, unit_price=100000, quantity=1)

        result = grant_premium_if_eligible(user)

        profile.refresh_from_db()
        assert result is profile
        assert profile.membership == MembershipLevel.PREMIUM
        assert profile.membership_granted_at is not None

    def test_stays_regular_at_or_below_threshold(self, settings):
        settings.PREMIUM_MEMBERSHIP_THRESHOLD = 100000
        user = UserFactory()
        profile = ProfileFactory(user=user)
        order = OrderFactory(user=user, status=OrderStatus.DELIVERED)
        OrderItemFactory(order=order, unit_price=100000, quantity=1)

        result = grant_premium_if_eligible(user)

        profile.refresh_from_db()
        assert result is None
        assert profile.membership == MembershipLevel.REGULAR

    def test_premium_is_not_revoked_and_grant_date_stays(self, settings):
        """Kolejne wywołanie — nawet poniżej progu — nie cofa premium ani daty."""
        settings.PREMIUM_MEMBERSHIP_THRESHOLD = 50000
        granted_at = timezone.now()
        user = UserFactory()
        profile = ProfileFactory(
            user=user,
            membership=MembershipLevel.PREMIUM,
            membership_granted_at=granted_at,
        )

        result = grant_premium_if_eligible(user)

        profile.refresh_from_db()
        assert result is None
        assert profile.membership == MembershipLevel.PREMIUM
        assert profile.membership_granted_at == granted_at

    def test_user_without_profile_is_ignored(self):
        user = UserFactory()

        assert grant_premium_if_eligible(user) is None


@pytest.mark.django_db
class TestIsPremium:
    def test_guest_is_never_premium(self):
        assert is_premium(None) is False

    def test_user_without_profile_is_not_premium(self):
        assert is_premium(UserFactory()) is False

    def test_regular_profile_is_not_premium(self):
        user = UserFactory()
        ProfileFactory(user=user, membership=MembershipLevel.REGULAR)

        assert is_premium(user) is False

    def test_premium_profile_is_premium(self):
        user = UserFactory()
        ProfileFactory(user=user, membership=MembershipLevel.PREMIUM)

        assert is_premium(user) is True
