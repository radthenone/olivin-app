"""Eksport danych osobowych klienta na wniosek (ADR 0029) — bez endpointu w API.

Użycie: `manage.py export_account_data <email> > eksport.json`.
"""

from __future__ import annotations

import json
from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db.models import Model
from django.forms.models import model_to_dict

from apps.accounts.models import Address, CustomUser, Profile
from apps.notifications.models import NotificationPreference


def _rows(objects: Any) -> list[dict[str, Any]]:
    return [model_to_dict(obj) for obj in objects]


def _row(obj: Model | None) -> dict[str, Any] | None:
    return model_to_dict(obj) if obj is not None else None


class Command(BaseCommand):
    help = "Eksportuje dane klienta (konto, profil, adresy, zamówienia, zgody, listy) jako JSON."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("email", help="Adres e-mail konta")

    def handle(self, *args: Any, **options: Any) -> None:
        user = CustomUser.objects.filter(email__iexact=options["email"]).first()
        if user is None:
            raise CommandError("Brak konta o tym adresie.")
        orders = user.orders.prefetch_related("items")  # type: ignore[missing-attribute]
        data = {
            "user": model_to_dict(
                user, exclude=["password", "groups", "user_permissions"]
            ),
            "profile": _row(Profile.objects.filter(user=user).first()),
            "addresses": _rows(Address.objects.filter(profile__user=user)),
            "orders": [
                {**model_to_dict(order), "items": _rows(order.items.all())}
                for order in orders
            ],
            "consents": _rows(user.consents.all()),  # type: ignore[missing-attribute]
            "reviews": _rows(user.reviews.all()),  # type: ignore[missing-attribute]
            "favorites": _rows(user.favorites.all()),  # type: ignore[missing-attribute]
            "watches": _rows(user.watches.all()),  # type: ignore[missing-attribute]
            "notification_preference": _row(
                NotificationPreference.objects.filter(user=user).first()
            ),
            "push_devices": _rows(user.push_devices.all()),  # type: ignore[missing-attribute]
        }
        self.stdout.write(json.dumps(data, ensure_ascii=False, indent=2, default=str))
