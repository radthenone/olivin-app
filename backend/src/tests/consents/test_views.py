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

    def test_anonim_dostaje_biezace_wersje(self, api_client: APIClient):
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

    def test_wersja_z_przyszlosci_nie_wychodzi(self, api_client: APIClient):
        ConsentDocumentFactory(version="2026-01")
        ConsentDocumentFactory(
            version="2099-01", effective_from=datetime.date(2099, 1, 1)
        )

        body = api_client.get(_documents_url()).json()

        assert [row["version"] for row in body] == ["2026-01"]

    def test_bez_dokumentow_lista_jest_pusta(self, api_client: APIClient):
        assert api_client.get(_documents_url()).json() == []


@pytest.mark.django_db
class TestRecordConsent:
    """`POST /consents/` — zgoda zalogowanego albo gościa po e-mailu."""

    def test_zalogowany_udziela_zgody_na_konto(
        self, authenticated_client: APIClient, user: CustomUser
    ):
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

    def test_gosc_udziela_zgody_po_emailu(self, api_client: APIClient):
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

    def test_gosc_bez_emaila_jest_odrzucony(self, api_client: APIClient):
        document = ConsentDocumentFactory()

        response: Any = api_client.post(
            _consents_url(), {"document": str(document.pk)}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.json()

    def test_zalogowany_z_emailem_jest_odrzucony(self, authenticated_client: APIClient):
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

    def test_zgoda_na_nieaktualna_wersje_jest_odrzucona(self, api_client: APIClient):
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

    def test_odpowiedz_nie_zdradza_emaila_ani_uzytkownika(self, api_client: APIClient):
        document = ConsentDocumentFactory()

        body = api_client.post(
            _consents_url(),
            {"document": str(document.pk), "email": "anna@example.com"},
            format="json",
        ).json()

        assert set(body) == {"id", "document", "kind", "version", "grantedAt"}

    def test_listy_zgod_nie_ma(self, authenticated_client: APIClient):
        """Zgody nie są zasobem do przeglądania przez API — panel je widzi."""
        response: Any = authenticated_client.get(_consents_url())

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
