from __future__ import annotations

from typing import Any, cast

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from apps.accounts.models import Profile
from apps.accounts.models.roles_model import RoleChoices
from tests.factories.accounts import ProfileFactory, UserFactory


@pytest.mark.django_db
class TestProfileViewSetAuth:
    """Testy autoryzacji ProfileViewSet."""

    def test_list_requires_authentication(self, api_client: APIClient):
        """GET list profili bez tokenu powinien zwrócić 403 (lub 401)."""
        response = cast(Response, api_client.get(reverse("profile-list")))
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]

    def test_list_with_authentication(self, authenticated_client: APIClient, user):
        """GET list profili z tokenem powinien zwrócić 200."""
        ProfileFactory(user=user)
        response = cast(Response, authenticated_client.get(reverse("profile-list")))
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestProfileViewSetList:
    """Testy listowania profili — izolacja między użytkownikami."""

    def test_user_sees_only_own_profile(self, api_client: APIClient):
        """Użytkownik powinien widzieć tylko swoje profile."""
        user1 = UserFactory()
        user2 = UserFactory()
        ProfileFactory(user=user1)
        ProfileFactory(user=user2)

        api_client.force_authenticate(user=user1)
        response = cast(Response, api_client.get(reverse("profile-list")))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1  # type: ignore
        assert response.data["results"][0]["email"] == user1.email  # type: ignore

    def test_empty_list_without_profile(self, authenticated_client: APIClient):
        """Lista profili powinna być pusta gdy użytkownik nie ma profilu."""
        response = cast(Response, authenticated_client.get(reverse("profile-list")))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0  # type: ignore
        assert response.data["results"] == []  # type: ignore


@pytest.mark.django_db
class TestProfileViewSetCreate:
    """Testy tworzenia profilu przez API."""

    def test_create_profile(self, authenticated_client: APIClient, user):
        """POST powinien tworzyć profil przypisany do zalogowanego użytkownika."""
        payload = {"first_name": "Jan", "last_name": "Kowalski"}
        response = cast(
            Response,
            authenticated_client.post(reverse("profile-list"), payload, format="json"),
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert Profile.objects.filter(user=user).exists()
        assert response.data["email"] == user.email  # type: ignore

    def test_create_profile_ignores_email_in_body(
        self, authenticated_client: APIClient, user
    ):
        """Email w body requestu powinien być ignorowany (read_only)."""
        payload = {
            "first_name": "Jan",
            "email": "hacker@evil.com",
        }
        response = cast(
            Response,
            authenticated_client.post(reverse("profile-list"), payload, format="json"),
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["email"] == user.email  # type: ignore


@pytest.mark.django_db
class TestProfileViewSetUpdate:
    """Testy aktualizacji profilu przez API."""

    def test_partial_update(self, authenticated_client: APIClient, user):
        """PATCH powinien aktualizować pola profilu."""
        profile = ProfileFactory(user=user, first_name="Stare")
        url = reverse("profile-detail", args=[profile.pk])
        response = cast(
            Response,
            authenticated_client.patch(url, {"first_name": "Nowe"}, format="json"),
        )
        assert response.status_code == status.HTTP_200_OK
        profile.refresh_from_db()
        assert profile.first_name == "Nowe"

    def test_user_cannot_edit_other_profile(self, api_client: APIClient):
        """PATCH cudzego profilu powinien zwrócić 404."""
        user1 = UserFactory()
        user2 = UserFactory()
        profile2 = ProfileFactory(user=user2)

        url = reverse("profile-detail", args=[profile2.pk])
        api_client.force_authenticate(user=user1)
        response = cast(
            Response, api_client.patch(url, {"first_name": "Zhack"}, format="json")
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestProfileViewSetChangeRole:
    """Testy akcji change-role."""

    def test_change_role_customer_to_admin(self, authenticated_client: APIClient, user):
        """PATCH change-role powinien przełączać rolę z CUSTOMER na ADMIN."""
        profile = ProfileFactory(user=user, role=RoleChoices.CUSTOMER)
        url = reverse("profile-change-role", args=[profile.pk])
        response = cast(Response, authenticated_client.patch(url))
        assert response.status_code == status.HTTP_200_OK
        profile.refresh_from_db()
        assert profile.role == RoleChoices.ADMIN

    def test_change_role_admin_to_customer(self, authenticated_client: APIClient, user):
        """PATCH change-role powinien przełączać rolę z ADMIN na CUSTOMER."""
        profile = ProfileFactory(user=user, role=RoleChoices.ADMIN)
        url = reverse("profile-change-role", args=[profile.pk])
        response = cast(Response, authenticated_client.patch(url))
        assert response.status_code == status.HTTP_200_OK
        profile.refresh_from_db()
        assert profile.role == RoleChoices.CUSTOMER


@pytest.mark.django_db
class TestProfilePendingConsents:
    """Profil zwraca zaległe zgody — okno akceptacji nowej wersji po zalogowaniu."""

    def test_profile_lists_pending_consents(
        self, authenticated_client: APIClient, user, consent_documents
    ):
        """Bez zgód → regulamin i polityka prywatności z wersją i id dokumentu."""
        profile = ProfileFactory(user=user)
        url = reverse("profile-detail", args=[profile.pk])

        response = cast(Response, authenticated_client.get(url))

        pending = cast(dict, response.data)["pending_consents"]
        assert [(p["kind"], p["version"]) for p in pending] == [
            ("terms", "terms-2026"),
            ("privacy", "privacy-2026"),
        ]
        assert pending[0]["id"] == str(consent_documents["terms"].pk)


@pytest.mark.django_db
class TestProfileDeliveryCountry:
    """Kraj dostawy w profilu — tylko państwa Unii, brak oznacza Polskę (#317)."""

    def _patch(self, client: APIClient, profile: Profile, country: str | None) -> Any:
        """PATCH profilu z podanym krajem dostawy."""
        url = reverse("profile-detail", args=[profile.pk])
        return client.patch(url, {"delivery_country": country}, format="json")

    def test_non_eu_country_is_rejected(self, authenticated_client: APIClient, user):
        """Kraj spoza Unii (US) → 400, profil bez zmian."""
        profile = ProfileFactory(user=user)

        response = self._patch(authenticated_client, profile, "US")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "delivery_country" in cast(dict, response.data)
        profile.refresh_from_db()
        assert not profile.delivery_country

    def test_blank_country_is_rejected(self, authenticated_client: APIClient, user):
        """Pusty string → 400; brak kraju zapisujemy tylko jako null."""
        profile = ProfileFactory(user=user, delivery_country="DE")

        response = self._patch(authenticated_client, profile, "")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        profile.refresh_from_db()
        assert profile.delivery_country == "DE"

    def test_eu_country_is_persisted_and_returned(
        self, authenticated_client: APIClient, user
    ):
        """Kraj Unii (DE) zapisuje się i wraca w odpowiedzi."""
        profile = ProfileFactory(user=user)

        response = self._patch(authenticated_client, profile, "DE")

        assert response.status_code == status.HTTP_200_OK
        assert cast(dict, response.data)["delivery_country"] == "DE"
        profile.refresh_from_db()
        assert profile.delivery_country == "DE"

    def test_poland_is_accepted(self, authenticated_client: APIClient, user):
        """Polska też jest krajem Unii — można ją wybrać wprost."""
        profile = ProfileFactory(user=user)

        response = self._patch(authenticated_client, profile, "PL")

        assert response.status_code == status.HTTP_200_OK
        assert cast(dict, response.data)["delivery_country"] == "PL"

    def test_profile_without_country_returns_null(
        self, authenticated_client: APIClient, user
    ):
        """Profil bez kraju zwraca null (klient traktuje to jako Polskę)."""
        profile = ProfileFactory(user=user)
        url = reverse("profile-detail", args=[profile.pk])

        response = cast(Response, authenticated_client.get(url))

        assert cast(dict, response.data)["delivery_country"] is None

    def test_country_can_be_cleared(self, authenticated_client: APIClient, user):
        """PATCH z null czyści kraj — powrót do domyślnej Polski."""
        profile = ProfileFactory(user=user, delivery_country="DE")

        response = self._patch(authenticated_client, profile, None)

        assert response.status_code == status.HTTP_200_OK
        assert cast(dict, response.data)["delivery_country"] is None
        profile.refresh_from_db()
        assert not profile.delivery_country
