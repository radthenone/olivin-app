"""Anonimizacja konta zamiast kasowania (#204, ADR 0029, `CONTEXT.md`).

Wymazuje dane osobowe konta, profilu i adresów, blokuje logowanie, kasuje
listy, urządzenia i preferencje. Zamówienia, dokumenty sprzedaży, zgody
i opinie zostają przypięte do konta, które nie ma już danych osobowych.
Nowy model trzymający dane klienta musi dopisać się tutaj.
"""

from __future__ import annotations

import logging
import uuid

from allauth.account.models import EmailAddress
from allauth.mfa.models import Authenticator
from allauth.socialaccount.models import SocialAccount
from django.contrib.sessions.models import Session
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import Address, CustomUser, Profile
from apps.favorites.models import Favorite
from apps.notifications.models import (
    NewsletterStatus,
    NewsletterSubscription,
    NotificationPreference,
    PushDevice,
)
from apps.orders.models import Cart, Order, OrderStatus
from apps.watches.models import Watch

logger = logging.getLogger(__name__)

# Zamówienie zakończone — każde inne blokuje anonimizację.
FINISHED_ORDER_STATUSES = (
    OrderStatus.DELIVERED,
    OrderStatus.CANCELLED,
    OrderStatus.RETURNED,
)
# Domena `.invalid` (RFC 2606) nigdy nie przyjmie poczty.
ANONYMISED_EMAIL_DOMAIN = "anonymised.invalid"


class ActiveOrderError(Exception):
    """Konto ma niedostarczone zamówienie — anonimizacja zablokowana."""


class StaffAccountError(Exception):
    """Konto obsługi sklepu — usuwa je administrator, nie samoobsługa."""


def has_active_order(user: CustomUser) -> bool:
    """Czy klient ma zamówienie w toku (poza dostarczonym, anulowanym, zwróconym)."""
    return (
        Order.objects.filter(user=user)
        .exclude(status__in=FINISHED_ORDER_STATUSES)
        .exists()
    )


@transaction.atomic
def anonymise_account(user: CustomUser) -> None:
    """Nieodwracalnie anonimizuje konto; `ActiveOrderError` przy trwającym zamówieniu.

    Zamówienia zostają w całości — numer, e-mail, odbiorca, adres dostawy,
    pozycje, ceny — razem z dokumentami sprzedaży. Prawo podatkowe (art. 112
    ustawy o VAT) wymaga przechowywania dokumentów i ewidencji do upływu
    przedawnienia zobowiązania podatkowego, czyli 5 lat od końca roku.
    Zamówienie zostaje przypięte do zanonimizowanego konta, a nie odpięte
    (`user=NULL`): ścieżka gościa po e-mailu i numerze otworzyłaby je.
    `StaffAccountError` dla konta obsługi sklepu.
    """
    user = CustomUser.objects.select_for_update().get(pk=user.pk)
    if user.is_staff or user.is_superuser:
        raise StaffAccountError
    if has_active_order(user):
        raise ActiveOrderError
    addresses = {user.email.lower()} | {
        email.lower()
        for email in EmailAddress.objects.filter(user=user).values_list(
            "email", flat=True
        )
    }

    EmailAddress.objects.filter(user=user).delete()
    SocialAccount.objects.filter(user=user).delete()
    Authenticator.objects.filter(user=user).delete()
    Address.objects.filter(profile__user=user).delete()
    Profile.objects.filter(user=user).update(
        first_name="",
        last_name="",
        date_of_birth=None,
        phone_number="",
        updated_at=timezone.now(),
    )
    Favorite.objects.filter(user=user).delete()
    Watch.objects.filter(user=user).delete()
    Cart.objects.filter(user=user).delete()
    PushDevice.objects.filter(user=user).delete()
    NotificationPreference.objects.filter(user=user).delete()
    # Subskrypcje trzymają adres małymi literami (`newsletter._normalise`).
    NewsletterSubscription.objects.filter(email__in=addresses).update(
        status=NewsletterStatus.UNSUBSCRIBED, updated_at=timezone.now()
    )
    _delete_sessions(user)

    user.email = f"{uuid.uuid4().hex}@{ANONYMISED_EMAIL_DOMAIN}"
    user.first_name = ""
    user.last_name = ""
    user.username = ""  # `save()` nada nowe `anon<liczba>`
    user.is_active = False
    user.set_unusable_password()
    user.save()
    logger.info("Konto %s zanonimizowane", user.pk)


def _delete_sessions(user: CustomUser) -> None:
    """Kasuje sesje konta (web i tokeny sesji aplikacji mobilnej)."""
    # ponytail: dekodowanie wszystkich żywych sesji — O(liczba sesji); przy
    # dużym ruchu tabela user→sesja (np. allauth.usersessions).
    user_pk = str(user.pk)
    stale = [
        session.pk
        for session in Session.objects.filter(expire_date__gt=timezone.now())
        if session.get_decoded().get("_auth_user_id") == user_pk
    ]
    Session.objects.filter(pk__in=stale).delete()
