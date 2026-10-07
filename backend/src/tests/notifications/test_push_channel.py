"""Kanał push w `notify()`: transakcyjne zawsze, marketing za zgodą (#202)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from apps.notifications.models import (
    Notification,
    NotificationKind,
    NotificationPreference,
    PushDevice,
)
from apps.notifications.services import notify
from core.integrations.push.fake import FakePushProvider
from tests.factories.accounts import UserFactory


@pytest.fixture
def push_provider(settings):
    """Atrapa adaptera push zamiast Expo — zapisuje wysyłki na klasie."""
    settings.PUSH_PROVIDER = "core.integrations.push.fake.FakePushProvider"
    FakePushProvider.reset()
    yield FakePushProvider
    FakePushProvider.reset()


def _device(user, token="ExponentPushToken[abc]"):
    return PushDevice.objects.create(user=user, token=token, platform="ios")


@pytest.mark.django_db
class TestNotifyPushTransactional:
    """Transakcyjny push do urządzeń klienta."""

    def test_queues_push_for_user_devices(
        self, django_capture_on_commit_callbacks, push_provider
    ):
        """Push jest kolejkowany na urządzenia klienta."""
        user = UserFactory()
        _device(user)

        with patch("apps.notifications.services.send_notification_email"):
            with django_capture_on_commit_callbacks(execute=True):
                notify(
                    user,
                    NotificationKind.ORDER_STATUS_CHANGED,
                    {"order_number": "ABC123", "status_label": "Wysłane"},
                )

        assert len(push_provider.sent) == 1
        sent = push_provider.sent[0]
        assert sent["tokens"] == ["ExponentPushToken[abc]"]
        assert "ABC123" in sent["title"] or "ABC123" in sent["body"]

    def test_no_devices_no_push(
        self, django_capture_on_commit_callbacks, push_provider
    ):
        """Bez urządzeń nie ma pusha."""
        user = UserFactory()

        with patch("apps.notifications.services.send_notification_email"):
            with django_capture_on_commit_callbacks(execute=True):
                notify(user, NotificationKind.ORDER_PAID, {"order_number": "X"})

        assert push_provider.sent == []

    def test_guest_gets_no_push(
        self, django_capture_on_commit_callbacks, push_provider
    ):
        """Gość nie dostaje pusha."""
        with patch("apps.notifications.services.send_notification_email"):
            with django_capture_on_commit_callbacks(execute=True):
                notify(
                    "guest@test.com",
                    NotificationKind.ORDER_STATUS_CHANGED,
                    {"order_number": "G1", "status_label": "Wysłane"},
                )

        assert push_provider.sent == []


@pytest.mark.django_db
class TestNotifyPushMarketing:
    """Marketingowy push wymaga zgody."""

    def test_skipped_without_push_consent(
        self, django_capture_on_commit_callbacks, push_provider
    ):
        """Bez zgody na push wysyłka jest pomijana."""
        user = UserFactory()
        _device(user)
        NotificationPreference.objects.create(
            user=user, marketing_email=True, marketing_push=False
        )

        with patch("apps.notifications.services.send_notification_email"):
            with django_capture_on_commit_callbacks(execute=True):
                notify(user, "promotion", {})

        assert push_provider.sent == []

    def test_sent_with_push_consent(
        self, django_capture_on_commit_callbacks, push_provider
    ):
        """Ze zgodą na push wysyłka idzie."""
        user = UserFactory()
        _device(user)
        NotificationPreference.objects.create(
            user=user, marketing_email=False, marketing_push=True
        )

        with patch("apps.notifications.services.send_notification_email"):
            with django_capture_on_commit_callbacks(execute=True):
                notify(user, "promotion", {})

        assert len(push_provider.sent) == 1


@pytest.mark.django_db
class TestPushDelivery:
    """Doręczenie pusha przez adapter."""

    def test_invalid_token_removed(
        self, django_capture_on_commit_callbacks, push_provider
    ):
        """Nieważny token jest usuwany."""
        user = UserFactory()
        _device(user, "ExponentPushToken[dead]")
        _device(user, "ExponentPushToken[live]")
        push_provider.invalid_tokens = ["ExponentPushToken[dead]"]

        with patch("apps.notifications.services.send_notification_email"):
            with django_capture_on_commit_callbacks(execute=True):
                notify(user, NotificationKind.ORDER_PAID, {"order_number": "X"})

        remaining = set(
            PushDevice.objects.filter(user=user).values_list("token", flat=True)
        )
        assert remaining == {"ExponentPushToken[live]"}

    def test_push_error_does_not_block_email(
        self, django_capture_on_commit_callbacks, push_provider
    ):
        """Błąd pusha nie blokuje e-maila."""
        user = UserFactory()
        _device(user)
        push_provider.fail_with = "Expo padło"

        with patch("apps.notifications.services.send_notification_email") as send_email:
            with django_capture_on_commit_callbacks(execute=True):
                notification = notify(
                    user, NotificationKind.ORDER_PAID, {"order_number": "X"}
                )

        send_email.assert_called_once()
        assert notification is not None
        assert Notification.objects.filter(user=user).exists()

    def test_push_body_and_data_override_email_content(
        self, django_capture_on_commit_callbacks, push_provider
    ):
        """Treść i dane pusha zastępują treść e-maila."""
        user = UserFactory()
        _device(user)

        with patch("apps.notifications.services.send_notification_email") as send_email:
            with django_capture_on_commit_callbacks(execute=True):
                notify(
                    user,
                    NotificationKind.ORDER_PAID,
                    {"order_number": "X"},
                    push_body="Krótko",
                    push_data={"type": "order_paid"},
                )

        assert push_provider.sent[0]["body"] == "Krótko"
        assert push_provider.sent[0]["data"] == {"type": "order_paid"}
        assert "X" in send_email.call_args.kwargs["body"]
