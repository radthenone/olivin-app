from __future__ import annotations

import json
import re
from typing import cast

import pytest
from rest_framework.response import Response
from rest_framework.test import APIClient

from apps.accounts.models import CustomUser

SIGNUP_URL = "/_allauth/app/v1/auth/signup"
REQUIRED_CONSENTS = {"consent_terms": True, "consent_privacy": True}
ANON_PATTERN = re.compile(r"^anon\d+$")

pytestmark = pytest.mark.django_db


def _signup(client: APIClient, email: str, **extra: object) -> Response:
    return cast(
        Response,
        client.post(
            SIGNUP_URL,
            {"email": email, "password": "testpass123!", **REQUIRED_CONSENTS, **extra},
            format="json",
        ),
    )


def _errors(response: Response) -> list[dict]:
    return json.loads(response.content)["errors"]


class TestSignupUsername:
    """Nazwa użytkownika wybrana przy rejestracji e-mailem."""

    def test_chosen_username_is_saved(self, api_client: APIClient, consent_documents):
        """Podana nazwa trafia na konto zamiast automatycznej `anon<liczba>`."""
        response = _signup(api_client, "named@test.com", username="olive_lover")

        assert response.status_code == 401
        user = CustomUser.objects.get(email="named@test.com")
        assert user.username == "olive_lover"

    def test_missing_username_falls_back_to_anon(
        self, api_client: APIClient, consent_documents
    ):
        """Bez nazwy konto dostaje automatyczną `anon<liczba>` (mobile bez zmian)."""
        _signup(api_client, "anon@test.com")

        user = CustomUser.objects.get(email="anon@test.com")
        assert ANON_PATTERN.match(user.username)

    def test_taken_username_is_reported_on_the_field(
        self, api_client: APIClient, consent_documents
    ):
        """Zajęta nazwa → 400 przy polu `username`, konto nie powstaje."""
        CustomUser.objects.create_user(
            email="existing@test.com", password="testpass123!", username="olive_lover"
        )

        response = _signup(api_client, "second@test.com", username="olive_lover")

        assert response.status_code == 400
        assert any(error.get("param") == "username" for error in _errors(response))
        assert not CustomUser.objects.filter(email="second@test.com").exists()

    def test_reserved_username_is_rejected(
        self, api_client: APIClient, consent_documents
    ):
        """Nazwa z prefiksem `anon` jest zarezerwowana dla konta automatycznego."""
        response = _signup(api_client, "reserved@test.com", username="anon12345678")

        assert response.status_code == 400
        assert any(error.get("param") == "username" for error in _errors(response))
        assert not CustomUser.objects.filter(email="reserved@test.com").exists()

    def test_username_with_forbidden_characters_is_rejected(
        self, api_client: APIClient, consent_documents
    ):
        """Znaki spoza `a-z 0-9 . _ -` są odrzucane tym samym walidatorem co w profilu."""
        response = _signup(api_client, "chars@test.com", username="jan kowalski")

        assert response.status_code == 400
        assert any(error.get("param") == "username" for error in _errors(response))
        assert not CustomUser.objects.filter(email="chars@test.com").exists()
