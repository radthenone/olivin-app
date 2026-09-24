"""Nadanie premium po progu dostarczonych zamówień (`CONTEXT.md`, Membership; ADR 0023)."""

from __future__ import annotations

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
    """Suma zapłacona za dostarczone zamówienia: po rabatach, bez dostawy, bez zwróconych.

    Zamówienie zwrócone ma status `returned`, nie `delivered` — filtr po
    statusie wystarcza, bez osobnego wykluczenia. Liczą się tylko zamówienia
    w złotych, bo próg jest ustawieniem w groszach PLN (ADR 0019: ceny
    źródłowe zawsze w złotych).
    # ponytail: zamówienia w euro pominięte, doliczyć po kursie gdy sprzedaż UE urośnie.
    """
    orders = Order.objects.filter(
        user=user, status=OrderStatus.DELIVERED, currency=DEFAULT_CURRENCY
    )
    zero = Money.zero(DEFAULT_CURRENCY)
    return sum(
        (order.goods_total - order.discount_money for order in orders), start=zero
    )


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
