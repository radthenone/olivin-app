"""Mail „konto już istnieje” w języku odbiorcy (#417, ADR 0035, ADR 0038)."""

from __future__ import annotations

from typing import cast

import pytest
from django.conf import settings
from django.core import mail
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from apps.accounts.models import Profile
from common.languages import PreferredLanguage
from tests.factories.accounts import ProfileFactory, UserFactory

SIGNUP_URL = "/_allauth/app/v1/auth/signup"
REQUIRED_CONSENTS = {"consent_terms": True, "consent_privacy": True}

pytestmark = pytest.mark.django_db


def _signup(client: APIClient, email: str, language: str | None = None) -> int:
    headers = {"HTTP_ACCEPT_LANGUAGE": language} if language else {}
    response = cast(
        Response,
        client.post(
            SIGNUP_URL,
            {"email": email, "password": "testpass123!", **REQUIRED_CONSENTS},
            format="json",
            **headers,
        ),
    )
    return response.status_code


def _existing_account(email: str, language: str | None) -> None:
    user = UserFactory(email=email)
    ProfileFactory(user=user, preferred_language=language)


class TestAccountAlreadyExistsMail:
    """Rejestracja zajętym adresem wysyła własny mail, zamiast szablonu allauth."""

    def test_polish_account_gets_polish_mail(
        self,
        api_client: APIClient,
        consent_documents,
        django_capture_on_commit_callbacks,
    ):
        """Konto z językiem polskim dostaje polski temat i treść z nazwą serwisu."""
        _existing_account("zajete@test.com", PreferredLanguage.PL)

        with django_capture_on_commit_callbacks(execute=True):
            status_code = _signup(api_client, "zajete@test.com")

        assert status_code == status.HTTP_401_UNAUTHORIZED
        assert len(mail.outbox) == 1
        message = mail.outbox[0]
        assert message.to == ["zajete@test.com"]
        assert "Konto już istnieje" in message.subject
        assert settings.SELLER_NAME in message.subject
        assert "Konto z adresem zajete@test.com już istnieje" in message.body
        assert settings.SELLER_NAME in message.body
        assert "Hello from" not in message.body

    def test_english_account_gets_english_mail(
        self,
        api_client: APIClient,
        consent_documents,
        django_capture_on_commit_callbacks,
    ):
        """Konto z językiem angielskim dostaje angielski mail i link `/en`."""
        _existing_account("taken@test.com", PreferredLanguage.EN)

        with django_capture_on_commit_callbacks(execute=True):
            _signup(api_client, "taken@test.com")

        message = mail.outbox[0]
        assert "Account Already Exists" in message.subject
        assert settings.SELLER_NAME in message.subject
        assert f"{settings.FRONTEND_URL}/en/account/reset-password" in message.body

    def test_reset_link_leads_to_web_code_reset(
        self,
        api_client: APIClient,
        consent_documents,
        django_capture_on_commit_callbacks,
    ):
        """Link do resetu prowadzi na stronę web resetu kodem, w języku konta."""
        _existing_account("reset@test.com", PreferredLanguage.PL)

        with django_capture_on_commit_callbacks(execute=True):
            _signup(api_client, "reset@test.com")

        expected = f"{settings.FRONTEND_URL}/pl/account/reset-password"
        assert expected in mail.outbox[0].body

    def test_language_falls_back_to_request(
        self,
        api_client: APIClient,
        consent_documents,
        django_capture_on_commit_callbacks,
    ):
        """Konto bez wybranego języka bierze język żądania, nie domyślny polski."""
        user = UserFactory(email="fallback@test.com")
        Profile.objects.filter(user=user).update(preferred_language=None)

        with django_capture_on_commit_callbacks(execute=True):
            _signup(api_client, "fallback@test.com", language="en-GB,en;q=0.9")

        assert "Account Already Exists" in mail.outbox[0].subject

    def test_no_language_anywhere_falls_back_to_polish(
        self,
        api_client: APIClient,
        consent_documents,
        django_capture_on_commit_callbacks,
    ):
        """Bez języka konta i żądania mail idzie po polsku."""
        user = UserFactory(email="domyslny@test.com")
        Profile.objects.filter(user=user).update(preferred_language=None)

        with django_capture_on_commit_callbacks(execute=True):
            _signup(api_client, "domyslny@test.com")

        assert "Konto już istnieje" in mail.outbox[0].subject
