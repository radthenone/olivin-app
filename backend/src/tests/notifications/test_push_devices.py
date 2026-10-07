"""API urządzeń push: rejestracja idempotentna, wyrejestrowanie (#202)."""

from __future__ import annotations

from typing import Any, cast

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from apps.notifications.models import PushDevice
from tests.factories.accounts import UserFactory


def _register_url() -> str:
    return reverse("push-device-list")


def _unregister_url(token: str) -> str:
    # `reverse` koduje token sam — wcześniejsze ręczne `quote()` podwójnie
    # kodowało nawiasy (`%255B`) i wyrejestrowanie chybiało.
    return reverse("push-device-detail", args=[token])


@pytest.mark.django_db
class TestPushDeviceRegistration:
    """Rejestracja urządzenia push."""

    def test_requires_authentication(self, api_client: APIClient):
        """Rejestracja wymaga zalogowania."""
        response = cast(
            Response,
            api_client.post(
                _register_url(),
                {"token": "ExponentPushToken[abc]", "platform": "ios"},
                format="json",
            ),
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_registers_device(self, authenticated_client: APIClient, user):
        """Urządzenie zostaje zarejestrowane."""
        response: Any = authenticated_client.post(
            _register_url(),
            {"token": "ExponentPushToken[abc]", "platform": "ios"},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert PushDevice.objects.filter(
            user=user, token="ExponentPushToken[abc]"
        ).exists()

    def test_registration_is_idempotent(self, authenticated_client: APIClient, user):
        """Powtórna rejestracja niczego nie dubluje."""
        payload = {"token": "ExponentPushToken[abc]", "platform": "ios"}
        first: Any = authenticated_client.post(_register_url(), payload, format="json")
        second: Any = authenticated_client.post(_register_url(), payload, format="json")

        assert first.status_code == status.HTTP_201_CREATED
        assert second.status_code == status.HTTP_201_CREATED
        assert PushDevice.objects.filter(token="ExponentPushToken[abc]").count() == 1

    def test_reregistration_moves_token_to_new_owner(
        self, authenticated_client: APIClient, user
    ):
        """Rejestracja na innym koncie przenosi token do nowego właściciela."""
        other = UserFactory()
        PushDevice.objects.create(
            user=other, token="ExponentPushToken[abc]", platform="android"
        )

        response: Any = authenticated_client.post(
            _register_url(),
            {"token": "ExponentPushToken[abc]", "platform": "ios"},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        device = PushDevice.objects.get(token="ExponentPushToken[abc]")
        assert device.user.pk == user.pk
        assert device.platform == "ios"

    def test_lists_only_own_devices(self, authenticated_client: APIClient, user):
        """Lista obejmuje tylko własne urządzenia."""
        other = UserFactory()
        PushDevice.objects.create(
            user=user, token="ExponentPushToken[mine]", platform="ios"
        )
        PushDevice.objects.create(
            user=other, token="ExponentPushToken[theirs]", platform="android"
        )

        response: Any = authenticated_client.get(_register_url())

        assert response.status_code == status.HTTP_200_OK
        tokens = [row["token"] for row in response.json()["results"]]
        assert tokens == ["ExponentPushToken[mine]"]


@pytest.mark.django_db
class TestPushDeviceUnregistration:
    """Wyrejestrowanie urządzenia push."""

    def test_unregisters_device(self, authenticated_client: APIClient, user):
        """Urządzenie zostaje wyrejestrowane."""
        PushDevice.objects.create(
            user=user, token="ExponentPushToken[abc]", platform="ios"
        )

        response: Any = authenticated_client.delete(
            _unregister_url("ExponentPushToken[abc]")
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not PushDevice.objects.filter(user=user).exists()

    def test_unregister_is_idempotent(self, authenticated_client: APIClient):
        """Powtórne wyrejestrowanie nie jest błędem."""
        response: Any = authenticated_client.delete(
            _unregister_url("ExponentPushToken[missing]")
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_cannot_unregister_someone_elses_device(
        self, authenticated_client: APIClient
    ):
        """Klient nie wyrejestruje cudzego urządzenia."""
        other = UserFactory()
        PushDevice.objects.create(
            user=other, token="ExponentPushToken[abc]", platform="ios"
        )

        response: Any = authenticated_client.delete(
            _unregister_url("ExponentPushToken[abc]")
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert PushDevice.objects.filter(token="ExponentPushToken[abc]").exists()
