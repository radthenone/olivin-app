from __future__ import annotations

import json
from typing import cast

import pytest
from rest_framework.response import Response
from rest_framework.test import APIClient

from apps.accounts.models import CustomUser, Profile
from apps.consents.models import Consent, ConsentKind
from apps.notifications.models import NotificationPreference
from tests.factories.consents import ConsentDocumentFactory

SIGNUP_URL = "/_allauth/app/v1/auth/signup"
REQUIRED_CONSENTS = {"consent_terms": True, "consent_privacy": True}

pytestmark = pytest.mark.django_db


def _signup(client: APIClient, email: str, **consents: bool) -> Response:
    return cast(
        Response,
        client.post(
            SIGNUP_URL,
            {"email": email, "password": "testpass123!", **consents},
            format="json",
        ),
    )


def _errors(response: Response) -> list[dict]:
    return json.loads(response.content)["errors"]


class TestEmailSignupConsents:
    """Rejestracja e-mailem wymaga zgód na regulamin i politykę prywatności."""

    def test_signup_with_required_consents_records_current_versions(
        self, api_client: APIClient, consent_documents
    ):
        """Komplet wymaganych zgód → konto, profil i Consent z bieżącą wersją."""
        _signup(api_client, "full@test.com", **REQUIRED_CONSENTS)

        user = CustomUser.objects.get(email="full@test.com")
        assert Profile.objects.filter(user=user).exists()
        consents = {c.kind: c.version for c in Consent.objects.filter(user=user)}
        assert consents == {"terms": "terms-2026", "privacy": "privacy-2026"}
        assert not NotificationPreference.for_user(user).marketing_email

    def test_signup_without_terms_is_rejected(
        self, api_client: APIClient, consent_documents
    ):
        """Bez zgody na regulamin → 400, konto nie powstaje."""
        response = _signup(api_client, "noterms@test.com", consent_privacy=True)

        assert response.status_code == 400
        assert any(e.get("param") == "consent_terms" for e in _errors(response))
        assert not CustomUser.objects.filter(email="noterms@test.com").exists()
        assert not Consent.objects.exists()

    def test_signup_with_marketing_sets_preference(
        self, api_client: APIClient, consent_documents
    ):
        """Zgoda marketingowa → Consent marketing i marketing_email=True."""
        _signup(api_client, "mkt@test.com", consent_marketing=True, **REQUIRED_CONSENTS)

        user = CustomUser.objects.get(email="mkt@test.com")
        kinds = set(
            Consent.objects.filter(user=user).values_list("document__kind", flat=True)
        )
        assert kinds == {"terms", "privacy", "marketing"}
        assert NotificationPreference.for_user(user).marketing_email

    def test_missing_current_document_rejects_signup(self, api_client: APIClient):
        """Brak bieżącej wersji regulaminu → czytelny błąd, konto nie powstaje."""
        ConsentDocumentFactory(kind=ConsentKind.PRIVACY)

        response = _signup(api_client, "nodoc@test.com", **REQUIRED_CONSENTS)

        assert response.status_code == 400
        assert any("konfiguracji" in e["message"] for e in _errors(response))
        assert not CustomUser.objects.filter(email="nodoc@test.com").exists()

    def test_missing_marketing_document_ignored_without_marketing_consent(
        self, api_client: APIClient
    ):
        """Brak dokumentu marketingowego nie blokuje rejestracji bez marketingu."""
        ConsentDocumentFactory(kind=ConsentKind.TERMS)
        ConsentDocumentFactory(kind=ConsentKind.PRIVACY)

        _signup(api_client, "nomkt@test.com", **REQUIRED_CONSENTS)

        assert CustomUser.objects.filter(email="nomkt@test.com").exists()

    def test_marketing_consent_without_marketing_document_is_rejected(
        self, api_client: APIClient
    ):
        """Zaznaczony marketing bez bieżącego dokumentu → błąd konfiguracji."""
        ConsentDocumentFactory(kind=ConsentKind.TERMS)
        ConsentDocumentFactory(kind=ConsentKind.PRIVACY)

        response = _signup(
            api_client, "badmkt@test.com", consent_marketing=True, **REQUIRED_CONSENTS
        )

        assert response.status_code == 400
        assert not CustomUser.objects.filter(email="badmkt@test.com").exists()
