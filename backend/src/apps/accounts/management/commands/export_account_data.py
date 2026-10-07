"""Eksport danych osobowych klienta na wniosek (ADR 0029) — bez endpointu w API.

Użycie: `manage.py export_account_data <email> > eksport.json`.
"""

from __future__ import annotations

import json
from typing import Any, Iterable

from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db.models import Model

from apps.accounts.models import Address, CustomUser, Profile
from apps.consents.models import Consent
from apps.favorites.models import Favorite
from apps.notifications.models import (
    NewsletterSubscription,
    Notification,
    NotificationPreference,
    PushDevice,
)
from apps.orders.models import Order, ReturnRequest, SalesDocument
from apps.reviews.models import Review
from apps.watches.models import Watch


def _row(obj: Model | None, exclude: Iterable[str] = ()) -> dict[str, Any] | None:
    """Wszystkie kolumny wiersza — także `editable=False`, których nie da `model_to_dict`."""
    if obj is None:
        return None
    return {
        field.attname: getattr(obj, field.attname)
        for field in obj._meta.concrete_fields
        if field.name not in exclude
    }


def _rows(objects: Iterable[Model]) -> list[dict[str, Any] | None]:
    return [_row(obj) for obj in objects]


class Command(BaseCommand):
    help = (
        "Eksportuje dane klienta (konto, profil, zamówienia, zgody, listy) jako JSON."
    )

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("email", help="Adres e-mail konta")

    def handle(self, *args: Any, **options: Any) -> None:
        user = CustomUser.objects.filter(email__iexact=options["email"]).first()
        if user is None:
            raise CommandError("Brak konta o tym adresie.")
        email_addresses = EmailAddress.objects.filter(user=user)
        addresses = {user.email.lower()} | {
            address.email.lower() for address in email_addresses
        }
        orders = Order.objects.filter(user=user).prefetch_related("items")
        data = {
            "user": _row(user, exclude=["password"]),
            "profile": _row(Profile.objects.filter(user=user).first()),
            "addresses": _rows(Address.objects.filter(profile__user=user)),
            "email_addresses": [
                {"email": a.email, "verified": a.verified, "primary": a.primary}
                for a in email_addresses
            ],
            "social_accounts": list(
                SocialAccount.objects.filter(user=user).values("provider", "uid")
            ),
            "orders": [
                {**(_row(order) or {}), "items": _rows(order.items.all())}  # type: ignore[missing-attribute]
                for order in orders
            ],
            "return_requests": _rows(ReturnRequest.objects.filter(order__user=user)),
            "sales_documents": _rows(SalesDocument.objects.filter(order__user=user)),
            "consents": _rows(Consent.objects.filter(user=user)),
            "reviews": _rows(Review.objects.filter(user=user)),
            "favorites": _rows(Favorite.objects.filter(user=user)),
            "watches": _rows(Watch.objects.filter(user=user)),
            "notification_preference": _row(
                NotificationPreference.objects.filter(user=user).first()
            ),
            "push_devices": _rows(PushDevice.objects.filter(user=user)),
            "notifications": _rows(Notification.objects.filter(user=user)),
            "newsletter_subscriptions": _rows(
                NewsletterSubscription.objects.filter(email__in=addresses)
            ),
        }
        self.stdout.write(json.dumps(data, ensure_ascii=False, indent=2, default=str))
