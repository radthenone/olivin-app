"""Nadanie premium po progu dostarczonych zamówień (`CONTEXT.md`, Membership; ADR 0023)."""

from __future__ import annotations

from decimal import ROUND_HALF_UP
from typing import TYPE_CHECKING

from django.conf import settings
from django.utils import timezone

from apps.accounts.models import MembershipLevel, Profile
from apps.orders.models import Order, OrderStatus
from common.money import DEFAULT_CURRENCY, Money

if TYPE_CHECKING:
    from apps.accounts.models import CustomUser


def is_premium(user: CustomUser | None) -> bool:
    """Czy klient ma premium — gość i konto bez profilu nigdy nie mają."""
    if user is None:
        return False
    profile = getattr(user, "profile", None)
    return profile is not None and profile.membership == MembershipLevel.PREMIUM


def paid_total(user: CustomUser) -> Money:
    """Suma faktycznie zapłacona za dostarczone zamówienia, bez dostawy.

    Ta sama formuła co `Order.total` bez dostawy: towar po rabatach i po
    kuponie, przycięty do zera. Kupon jest formą zapłaty (ADR 0011/0014) —
    kupon wydany ze zwrotu pochodzi z kwoty już raz policzonej do progu przy
    poprzednim zamówieniu, więc pokryta nim część nie jest zapłatą drugi raz.

    Zamówienie zwrócone ma status `returned`, nie `delivered` — filtr po
    statusie wystarcza, bez osobnego wykluczenia. Próg jest w groszach PLN,
    więc zamówienie w euro wraca do złotych po kursie zapisanym w nim
    samym (ADR 0019), zaokrąglone do grosza.
    """
    orders = Order.objects.filter(user=user, status=OrderStatus.DELIVERED)
    zero = Money.zero(DEFAULT_CURRENCY)
    total = zero
    for order in orders:
        goods = order.goods_total - order.discount_money - order.coupon_money
        if goods.currency != DEFAULT_CURRENCY:
            goods = Money(
                goods.multiply(order.exchange_rate, rounding=ROUND_HALF_UP).amount,
                DEFAULT_CURRENCY,
            )
        total += goods if goods > zero else zero
    return total


def grant_premium_if_eligible(user: CustomUser) -> Profile | None:
    """Nadaje premium bezterminowo, gdy suma dostarczonych zamówień przekroczy próg.

    Premium nigdy nie jest odbierane — funkcja tylko nadaje, nigdy nie cofa.
    """
    profile = getattr(user, "profile", None)
    if profile is None or profile.membership == MembershipLevel.PREMIUM:
        return None
    if paid_total(user).amount <= settings.PREMIUM_MEMBERSHIP_THRESHOLD:
        return None
    profile.membership = MembershipLevel.PREMIUM
    profile.membership_granted_at = timezone.now()
    profile.save(update_fields=["membership", "membership_granted_at", "updated_at"])
    return profile
