"""Eksport danych klienta na wniosek — polecenie zarządzające (#204, ADR 0029)."""

from __future__ import annotations

import json
from io import StringIO

import pytest
from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount
from django.core.management import CommandError, call_command

from apps.notifications.models import NewsletterSubscription
from tests.factories.accounts import ProfileFactory, UserFactory
from tests.factories.consents import ConsentFactory
from tests.factories.favorites import FavoriteFactory
from tests.factories.orders import OrderFactory

pytestmark = pytest.mark.django_db


def export(email: str) -> dict:
    """Eksportuje dane konta do słownika."""
    out = StringIO()
    call_command("export_account_data", email, stdout=out)
    return json.loads(out.getvalue())


def test_exports_account_data_without_password() -> None:
    """Eksport zawiera dane konta bez hasła."""
    user = UserFactory(email="jan@test.com", first_name="Jan")
    ProfileFactory(user=user, last_name="Kowalski")
    OrderFactory(user=user)
    ConsentFactory(user=user)
    FavoriteFactory(user=user)
    FavoriteFactory()

    data = export("JAN@test.com")

    assert data["user"]["email"] == "jan@test.com"
    assert data["user"]["first_name"] == "Jan"
    assert "password" not in data["user"]
    assert data["profile"]["last_name"] == "Kowalski"
    assert len(data["orders"]) == 1
    assert len(data["consents"]) == 1
    assert len(data["favorites"]) == 1


def test_unknown_account_fails() -> None:
    """Eksport nieistniejącego konta kończy się błędem."""
    with pytest.raises(CommandError):
        export("nobody@test.com")


def test_exports_non_editable_fields_and_related_records() -> None:
    """Eksport obejmuje pola nieedytowalne i powiązane rekordy."""
    user = UserFactory(email="ola@test.com")
    order = OrderFactory(user=user)
    EmailAddress.objects.create(user=user, email="ola@test.com", verified=True)
    SocialAccount.objects.create(
        user=user, provider="google", uid="g-7", extra_data={"token": "secret"}
    )
    NewsletterSubscription.objects.create(email="ola@test.com")

    data = export("ola@test.com")

    assert data["orders"][0]["number"] == order.number
    assert data["email_addresses"][0]["email"] == "ola@test.com"
    assert data["social_accounts"] == [{"provider": "google", "uid": "g-7"}]
    assert data["newsletter_subscriptions"][0]["email"] == "ola@test.com"
    for key in ("notifications", "return_requests", "sales_documents"):
        assert data[key] == []
