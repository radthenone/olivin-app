from __future__ import annotations

import re
from typing import cast
from unittest.mock import patch

import pytest
from allauth.account.adapter import get_adapter
from allauth.socialaccount.models import SocialAccount, SocialLogin
from django.forms import BaseForm
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from apps.accounts.models import CustomUser
from apps.accounts.usernames import generate_anon_username
from core.services.allauth.social_adapter import SocialAccountAdapter
from tests.factories.accounts import ProfileFactory, UserFactory

ANON_PATTERN = re.compile(r"^anon\d+$")


class SignupFormStub:
    """Adapter czyta z formularza wyłącznie `cleaned_data`."""

    cleaned_data = {"email": "anon-signup@test.com", "password1": "testpass123!"}


def test_generate_anon_username_format():
    """Generator zwraca `anon` + liczba."""
    assert ANON_PATTERN.match(generate_anon_username())


@pytest.mark.django_db
class TestAnonUsernameOnSave:
    """Nazwa `anon<liczba>` nadawana przy zapisie konta bez nazwy."""

    def test_user_without_username_gets_anon_name(self):
        """Konto bez nazwy dostaje unikalną nazwę `anon<liczba>`."""
        first = CustomUser.objects.create_user(email="a@test.com", password="pass")
        second = UserFactory(username=None)

        assert ANON_PATTERN.match(first.username)
        assert ANON_PATTERN.match(second.username)
        assert first.username != second.username

    def test_chosen_username_is_kept(self):
        """Wybrana nazwa nie jest nadpisywana."""
        user = UserFactory(username="olive_lover")
        assert user.username == "olive_lover"

    def test_existing_name_collision_retries(self):
        """Kolizja z istniejącą nazwą (także inną wielkością liter) → nowa próba."""
        UserFactory(username="ANON1")
        with patch(
            "apps.accounts.models.user_model.generate_anon_username",
            side_effect=["anon1", "anon2"],
        ):
            user = UserFactory(username=None)
        assert user.username == "anon2"

    def test_insert_race_retries(self):
        """IntegrityError z wyścigu na unikalności nazwy → nowa próba."""
        UserFactory(username="anon1")
        with (
            patch(
                "apps.accounts.models.user_model.CustomUser._anon_username_taken",
                # przed zapisem wolna, po IntegrityError zajęta, następna wolna
                side_effect=[False, True, False],
            ),
            patch(
                "apps.accounts.models.user_model.generate_anon_username",
                side_effect=["anon1", "anon2"],
            ),
        ):
            user = UserFactory(username=None)
        assert user.username == "anon2"

    def test_other_integrity_error_is_not_swallowed(self):
        """Duplikat e-maila dalej rzuca IntegrityError."""
        from django.db import IntegrityError

        UserFactory(email="dup-anon@test.com")
        with pytest.raises(IntegrityError):
            CustomUser(email="dup-anon@test.com").save()


@pytest.mark.django_db
class TestAnonUsernameOnSignup:
    """Rejestracja e-mailem i kontem społecznościowym nadaje nazwę `anon`."""

    def test_email_signup_assigns_anon_username(self, rf):
        """Signup e-mailem nie wyprowadza nazwy z adresu e-mail."""
        user = cast(
            CustomUser,
            get_adapter().save_user(
                rf.post("/"), CustomUser(), cast(BaseForm, SignupFormStub())
            ),
        )
        user.refresh_from_db()
        assert ANON_PATTERN.match(user.username)

    def test_headless_signup_assigns_anon_username(self, api_client: APIClient):
        """Rejestracja headless nadaje nazwę `anon<liczba>`."""
        api_client.post(
            "/_allauth/app/v1/auth/signup",
            {"email": "headless-anon@test.com", "password": "testpass123!"},
            format="json",
        )
        user = CustomUser.objects.get(email="headless-anon@test.com")
        assert ANON_PATTERN.match(user.username)

    def test_social_signup_assigns_anon_username(self, rf):
        """Konto społecznościowe dostaje nazwę `anon<liczba>`, nie z danych dostawcy."""
        request = rf.get("/")
        request.session = {}
        sociallogin = SocialLogin(
            user=CustomUser(),
            account=SocialAccount(provider="google", uid="anon-social-1"),
        )
        adapter = SocialAccountAdapter()
        adapter.populate_user(
            request,
            sociallogin,
            {"email": "social-anon@test.com", "name": "Jan Kowalski"},
        )

        user = cast(CustomUser, adapter.save_user(request, sociallogin))

        user.refresh_from_db()
        assert ANON_PATTERN.match(user.username)
        assert user.email == "social-anon@test.com"


@pytest.mark.django_db
class TestUsernameChangeInProfile:
    """Klient zmienia nazwę przez PATCH profilu."""

    def _patch(self, client: APIClient, user: CustomUser, username: str) -> Response:
        profile = ProfileFactory(user=user)
        client.force_authenticate(user=user)
        url = reverse("profile-detail", args=[profile.pk])
        return cast(Response, client.patch(url, {"username": username}, format="json"))

    def test_change_username(self, api_client: APIClient):
        """Poprawna nazwa zapisuje się na koncie i wraca w odpowiedzi."""
        user = UserFactory(username=None)
        response = self._patch(api_client, user, "olive.lover-1")

        assert response.status_code == status.HTTP_200_OK
        assert cast(dict, response.data)["username"] == "olive.lover-1"
        user.refresh_from_db()
        assert user.username == "olive.lover-1"

    def test_keep_own_username(self, api_client: APIClient):
        """Wysłanie własnej obecnej nazwy nie jest kolizją."""
        user = UserFactory(username="Mine")
        assert self._patch(api_client, user, "mine").status_code == 200

    def test_taken_username_rejected_case_insensitive(self, api_client: APIClient):
        """Nazwa zajęta (bez względu na wielkość liter) → 400."""
        UserFactory(username="Taken")
        user = UserFactory(username=None)
        response = self._patch(api_client, user, "taken")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "username" in cast(dict, response.data)

    @pytest.mark.parametrize("bad", ["ab", "with space", "zażółć", "a" * 31, "x@y"])
    def test_invalid_username_rejected(self, api_client: APIClient, bad: str):
        """Niedozwolone znaki lub długość → 400, nazwa bez zmian."""
        user = UserFactory(username=None)
        before = user.username
        response = self._patch(api_client, user, bad)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        user.refresh_from_db()
        assert user.username == before


@pytest.mark.django_db
def test_migration_fills_empty_usernames_and_keeps_chosen():
    """Migracja 0004 nadaje `anon` kontom z pustą nazwą i nie rusza wybranych.

    Testy działają bez migracji, więc woła się funkcję migracji wprost; pustą
    nazwę wstawia się z pominięciem CHECK (po migracji 0005 pusta jest zakazana).
    """
    import importlib

    from django.apps import apps
    from django.db import connection

    migration = importlib.import_module(
        "apps.accounts.migrations.0004_fill_empty_usernames"
    )
    blank = UserFactory(email="blank@test.com")
    chosen = UserFactory(email="chosen@test.com", username="Chosen")
    table = CustomUser._meta.db_table
    with connection.cursor() as cursor:
        if connection.vendor == "sqlite":
            cursor.execute("PRAGMA ignore_check_constraints = 1")
        else:
            cursor.execute(
                f"ALTER TABLE {table} DROP CONSTRAINT accounts_user_username_not_empty"
            )
        try:
            cursor.execute(
                f"UPDATE {table} SET username = '' WHERE id = %s", [blank.pk]
            )
        finally:
            if connection.vendor == "sqlite":
                cursor.execute("PRAGMA ignore_check_constraints = 0")

    migration.fill_empty_usernames(apps, None)

    blank.refresh_from_db()
    chosen.refresh_from_db()
    assert ANON_PATTERN.match(blank.username)
    assert chosen.username == "Chosen"
