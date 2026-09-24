"""API: `GET /notifications/`, `POST /notifications/{id}/read/`, preferencje (#156)."""

from __future__ import annotations

from typing import Any, cast

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from apps.notifications.models import Notification, NotificationKind
from tests.factories.accounts import UserFactory


def _notification(user, kind=NotificationKind.ORDER_STATUS_CHANGED) -> Notification:
    return Notification.objects.create(user=user, kind=kind, message="test", data={})


@pytest.mark.django_db
class TestNotificationList:
    def test_requires_authentication(self, api_client: APIClient):
        response = cast(Response, api_client.get(reverse("notification-list")))
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_lists_only_own_notifications(self, authenticated_client: APIClient, user):
        other = UserFactory()
        mine = _notification(user)
        _notification(other)

        response: Any = authenticated_client.get(reverse("notification-list"))

        assert response.status_code == status.HTTP_200_OK
        ids = [row["id"] for row in response.json()["results"]]
        assert ids == [str(mine.id)]


@pytest.mark.django_db
class TestNotificationRead:
    def test_marks_notification_as_read(self, authenticated_client: APIClient, user):
        notification = _notification(user)

        url = reverse("notification-read", args=[notification.id])
        response: Any = authenticated_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        notification.refresh_from_db()
        assert notification.is_read is True
        assert notification.read_at is not None

    def test_cannot_read_someone_elses_notification(
        self, authenticated_client: APIClient
    ):
        other = UserFactory()
        notification = _notification(other)

        url = reverse("notification-read", args=[notification.id])
        response: Any = authenticated_client.post(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestNotificationPreferences:
    def test_default_preferences_have_no_marketing_consent(
        self, authenticated_client: APIClient
    ):
        response: Any = authenticated_client.get(reverse("notification-preferences"))

        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert body["marketingEmail"] is False
        assert body["marketingPush"] is False

    def test_updates_preferences(self, authenticated_client: APIClient):
        response: Any = authenticated_client.put(
            reverse("notification-preferences"),
            {"marketingEmail": True, "marketingPush": False},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["marketingEmail"] is True

        again: Any = authenticated_client.get(reverse("notification-preferences"))
        assert again.json()["marketingEmail"] is True
