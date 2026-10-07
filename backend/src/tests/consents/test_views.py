"""Testy API zgód na realnym kształcie odpowiedzi (`response.json()`, camelCase)."""

from __future__ import annotations

import datetime
from typing import Any

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import CustomUser
from apps.consents.models import Consent, ConsentKind
from tests.factories.consents import ConsentDocumentFactory


def _documents_url() -> str:
    return reverse("consent-document-list")


def _consents_url() -> str:
    return reverse("consent-list")


@pytest.mark.django_db
class TestCurrentDocuments:
    """`GET /consents/documents/` — po jednej bieżącej wersji na rodzaj, dla każdego."""

    def test_anonymous_gets_current_versions(self, api_client: APIClient):
        """Anonim dostaje bieżące wersje dokumentów."""
        ConsentDocumentFactory(
            kind=ConsentKind.TERMS,
            version="2026-01",
            effective_from=datetime.date(2026, 1, 1),
        )
        ConsentDocumentFactory(
            kind=ConsentKind.TERMS,
            version="2026-06",
            effective_from=datetime.date(2026, 6, 1),
        )
        ConsentDocumentFactory(kind=ConsentKind.PRIVACY, version="2026-01")

        response: Any = api_client.get(_documents_url())

        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert [(row["kind"], row["version"]) for row in body] == [
            ("terms", "2026-06"),
            ("privacy", "2026-01"),
        ]
        assert body[0]["effectiveFrom"] == "2026-06-01"
        assert "id" in body[0]

    def test_future_version_is_not_listed(self, api_client: APIClient):
        """Wersja z przyszłości nie wychodzi na listę."""
        ConsentDocumentFactory(version="2026-01")
        ConsentDocumentFactory(
            version="2099-01", effective_from=datetime.date(2099, 1, 1)
        )

        response: Any = api_client.get(_documents_url())

        assert [row["version"] for row in response.json()] == ["2026-01"]

    def test_without_documents_list_is_empty(self, api_client: APIClient):
        """Bez dokumentów lista jest pusta."""
        response: Any = api_client.get(_documents_url())

        assert response.json() == []


@pytest.mark.django_db
class TestRecordConsent:
    """`POST /consents/` — zgoda zalogowanego albo gościa po e-mailu."""

    def test_logged_in_consents_for_account(
        self, authenticated_client: APIClient, user: CustomUser
    ):
        """Zalogowany udziela zgody na konto."""
        document = ConsentDocumentFactory(version="2026-06")

        response: Any = authenticated_client.post(
            _consents_url(), {"document": str(document.pk)}, format="json"
        )

        assert response.status_code == status.HTTP_201_CREATED
        body = response.json()
        assert body["kind"] == "terms"
        assert body["version"] == "2026-06"
        assert body["grantedAt"]
        assert Consent.objects.has_current_consent(ConsentKind.TERMS, user=user)

    def test_guest_consents_by_email(self, api_client: APIClient):
        """Gość udziela zgody po adresie e-mail."""
        document = ConsentDocumentFactory()

        response: Any = api_client.post(
            _consents_url(),
            {"document": str(document.pk), "email": "anna@example.com"},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert Consent.objects.has_current_consent(
            ConsentKind.TERMS, email="anna@example.com"
        )

    def test_guest_without_email_is_rejected(self, api_client: APIClient):
        """Gość bez e-maila jest odrzucany."""
        document = ConsentDocumentFactory()

        response: Any = api_client.post(
            _consents_url(), {"document": str(document.pk)}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.json()

    def test_logged_in_with_email_is_rejected(self, authenticated_client: APIClient):
        """Podmiot jest dokładnie jeden — e-mail przy koncie to niejasność,
        nie wygoda."""
        document = ConsentDocumentFactory()

        response: Any = authenticated_client.post(
            _consents_url(),
            {"document": str(document.pk), "email": "anna@example.com"},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.json()
        assert not Consent.objects.exists()

    def test_consent_to_outdated_version_is_rejected(self, api_client: APIClient):
        """Klient pokazał starą wersję — musi odświeżyć listę, nie zapisać
        zgody, która i tak nie byłaby aktualna."""
        stale = ConsentDocumentFactory(
            version="2026-01", effective_from=datetime.date(2026, 1, 1)
        )
        ConsentDocumentFactory(
            version="2026-06", effective_from=datetime.date(2026, 6, 1)
        )

        response: Any = api_client.post(
            _consents_url(),
            {"document": str(stale.pk), "email": "anna@example.com"},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "document" in response.json()

    def test_response_does_not_reveal_email_or_user(self, api_client: APIClient):
        """Odpowiedź nie zdradza e-maila ani użytkownika."""
        document = ConsentDocumentFactory()

        response: Any = api_client.post(
            _consents_url(),
            {"document": str(document.pk), "email": "anna@example.com"},
            format="json",
        )

        assert set(response.json()) == {
            "id",
            "document",
            "kind",
            "version",
            "grantedAt",
        }

    def test_consent_list_does_not_exist(self, authenticated_client: APIClient):
        """Zgody nie są zasobem do przeglądania przez API — panel je widzi."""
        response: Any = authenticated_client.get(_consents_url())

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
