"""Eksport danych klienta na wniosek — polecenie zarządzające (#204, ADR 0029)."""

from __future__ import annotations

import json
from io import StringIO

import pytest
from django.core.management import CommandError, call_command

from tests.factories.accounts import ProfileFactory, UserFactory
from tests.factories.consents import ConsentFactory
from tests.factories.favorites import FavoriteFactory
from tests.factories.orders import OrderFactory

pytestmark = pytest.mark.django_db


def export(email: str) -> dict:
    out = StringIO()
    call_command("export_account_data", email, stdout=out)
    return json.loads(out.getvalue())


def test_exports_account_data_without_password() -> None:
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
    with pytest.raises(CommandError):
        export("nobody@test.com")
