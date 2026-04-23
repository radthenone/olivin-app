from __future__ import annotations

from typing import cast

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

    def test_list_wymaga_autoryzacji(self, api_client: APIClient):
        """GET list profili bez tokenu powinien zwrócić 403 (lub 401)."""
        response = cast(Response, api_client.get(reverse("profile-list")))
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]

    def test_list_z_autoryzacja(self, authenticated_client: APIClient, user):
        """GET list profili z tokenem powinien zwrócić 200."""
        ProfileFactory(user=user)
        response = cast(Response, authenticated_client.get(reverse("profile-list")))
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestProfileViewSetList:
    """Testy listowania profili — izolacja między użytkownikami."""

    def test_user_widzi_tylko_swoj_profil(self, api_client: APIClient):
        """Użytkownik powinien widzieć tylko swoje profile."""
        user1 = UserFactory()
        user2 = UserFactory()
        ProfileFactory(user=user1)
        ProfileFactory(user=user2)

        api_client.force_authenticate(user=user1)
        response = cast(Response, api_client.get(reverse("profile-list")))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1  # type: ignore
        assert response.data[0]["email"] == user1.email  # type: ignore

    def test_pusta_lista_gdy_brak_profilu(self, authenticated_client: APIClient):
        """Lista profili powinna być pusta gdy użytkownik nie ma profilu."""
        response = cast(Response, authenticated_client.get(reverse("profile-list")))
        assert response.status_code == status.HTTP_200_OK
        assert response.data == []  # type: ignore


@pytest.mark.django_db
class TestProfileViewSetCreate:
    """Testy tworzenia profilu przez API."""

    def test_create_profil(self, authenticated_client: APIClient, user):
        """POST powinien tworzyć profil przypisany do zalogowanego użytkownika."""
        payload = {"first_name": "Jan", "last_name": "Kowalski"}
        response = cast(
            Response,
            authenticated_client.post(reverse("profile-list"), payload, format="json"),
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert Profile.objects.filter(user=user).exists()
        assert response.data["email"] == user.email  # type: ignore

    def test_create_profil_ignoruje_email_z_body(
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

    def test_user_nie_moze_edytowac_cudzego_profilu(self, api_client: APIClient):
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

    def test_zmiana_roli_customer_na_admin(self, authenticated_client: APIClient, user):
        """PATCH change-role powinien przełączać rolę z CUSTOMER na ADMIN."""
        profile = ProfileFactory(user=user, role=RoleChoices.CUSTOMER)
        url = reverse("profile-change-role", args=[profile.pk])
        response = cast(Response, authenticated_client.patch(url))
        assert response.status_code == status.HTTP_200_OK
        profile.refresh_from_db()
        assert profile.role == RoleChoices.ADMIN

    def test_zmiana_roli_admin_na_customer(self, authenticated_client: APIClient, user):
        """PATCH change-role powinien przełączać rolę z ADMIN na CUSTOMER."""
        profile = ProfileFactory(user=user, role=RoleChoices.ADMIN)
        url = reverse("profile-change-role", args=[profile.pk])
        response = cast(Response, authenticated_client.patch(url))
        assert response.status_code == status.HTTP_200_OK
        profile.refresh_from_db()
        assert profile.role == RoleChoices.CUSTOMER
