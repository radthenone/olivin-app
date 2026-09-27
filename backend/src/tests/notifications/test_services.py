"""`notify()` — rekord dla klienta, e-mail zawsze, marketing za zgodą (#156)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from apps.notifications.models import (
    Notification,
    NotificationKind,
    NotificationPreference,
)
from apps.notifications.services import notify
from tests.factories.accounts import UserFactory


@pytest.mark.django_db
class TestNotifyTransactional:
    """Transakcyjne (status/paid/dokument) docierają zawsze, bez pytania o zgodę."""

    def test_creates_record_and_queues_email_for_user(
        self, django_capture_on_commit_callbacks
    ):
        user = UserFactory()

        with patch("apps.notifications.services.send_notification_email") as send:
            with django_capture_on_commit_callbacks(execute=True):
                notification = notify(
                    user,
                    NotificationKind.ORDER_STATUS_CHANGED,
                    {"order_number": "ABC123", "status_label": "Wysłane"},
                )

        assert notification is not None
        assert Notification.objects.filter(user=user).count() == 1
        stored = Notification.objects.get(user=user)
        assert stored.kind == NotificationKind.ORDER_STATUS_CHANGED
        assert "ABC123" in stored.message
        assert stored.data == {"order_number": "ABC123", "status_label": "Wysłane"}
        send.assert_called_once()
        assert send.call_args.kwargs["to"] == user.email

    def test_ignores_marketing_preference(self, django_capture_on_commit_callbacks):
        """Transakcyjne docierają nawet bez zgody marketingowej — nie jej dotyczy."""
        user = UserFactory()
        NotificationPreference.objects.create(user=user, marketing_email=False)

        with patch("apps.notifications.services.send_notification_email") as send:
            with django_capture_on_commit_callbacks(execute=True):
                notify(user, NotificationKind.ORDER_PAID, {"order_number": "X"})

        send.assert_called_once()
        assert Notification.objects.filter(user=user).exists()

    def test_guest_gets_only_email_no_record(self, django_capture_on_commit_callbacks):
        """Gość (e-mail zamiast konta) dostaje e-mail, bez rekordu w aplikacji."""
        with patch("apps.notifications.services.send_notification_email") as send:
            with django_capture_on_commit_callbacks(execute=True):
                result = notify(
                    "guest@test.com",
                    NotificationKind.ORDER_STATUS_CHANGED,
                    {"order_number": "G1", "status_label": "Wysłane"},
                )

        assert result is None
        assert Notification.objects.count() == 0
        send.assert_called_once()
        assert send.call_args.kwargs["to"] == "guest@test.com"


@pytest.mark.django_db
class TestNotifyMarketing:
    """Rodzaje spoza `TRANSACTIONAL_KINDS` respektują zgodę marketingową."""

    def test_skipped_without_consent(self, django_capture_on_commit_callbacks):
        user = UserFactory()
        NotificationPreference.objects.create(user=user, marketing_email=False)

        with patch("apps.notifications.services.send_notification_email") as send:
            with django_capture_on_commit_callbacks(execute=True):
                result = notify(user, "promotion", {})

        assert result is None
        send.assert_not_called()
        assert Notification.objects.count() == 0

    def test_skipped_when_no_preference_recorded_yet(
        self, django_capture_on_commit_callbacks
    ):
        """Brak wpisu preferencji = brak zgody (domyślnie `False`)."""
        user = UserFactory()

        with patch("apps.notifications.services.send_notification_email") as send:
            with django_capture_on_commit_callbacks(execute=True):
                result = notify(user, "promotion", {})

        assert result is None
        send.assert_not_called()

    def test_sent_with_consent(self, django_capture_on_commit_callbacks):
        user = UserFactory()
        NotificationPreference.objects.create(user=user, marketing_email=True)

        with patch("apps.notifications.services.send_notification_email") as send:
            with django_capture_on_commit_callbacks(execute=True):
                result = notify(user, "promotion", {})

        assert result is not None
        send.assert_called_once()

    def test_guest_never_gets_marketing(self, django_capture_on_commit_callbacks):
        with patch("apps.notifications.services.send_notification_email") as send:
            with django_capture_on_commit_callbacks(execute=True):
                result = notify("guest@test.com", "promotion", {})

        assert result is None
        send.assert_not_called()
