"""Podpięcie powiadomień: zmiana statusu, `paid`, dokument gotowy (#156)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from apps.notifications.models import Notification, NotificationKind
from apps.orders.models import OrderStatus, SalesDocumentKind
from apps.orders.services.document import issue_document
from tests.factories.orders import GuestOrderFactory, OrderFactory, OrderItemFactory


@pytest.mark.django_db
class TestOrderStatusChangeNotifies:
    def test_transition_creates_notification_and_email_for_user(
        self, django_capture_on_commit_callbacks
    ):
        order = OrderFactory(status=OrderStatus.PENDING)

        with patch("apps.notifications.services.send_notification_email") as send:
            with django_capture_on_commit_callbacks(execute=True):
                order.transition_to(OrderStatus.PAID)

        assert order.user is not None
        notification = Notification.objects.get(user=order.user)
        assert notification.kind == NotificationKind.ORDER_PAID
        assert notification.data["order_number"] == order.number
        send.assert_called_once()
        assert send.call_args.kwargs["to"] == order.user.email

    def test_non_paid_transition_uses_status_changed_kind(
        self, django_capture_on_commit_callbacks
    ):
        order = OrderFactory(status=OrderStatus.PAID)

        with patch("apps.notifications.services.send_notification_email"):
            with django_capture_on_commit_callbacks(execute=True):
                order.transition_to(OrderStatus.PACKED)

        notification = Notification.objects.get(user=order.user)
        assert notification.kind == NotificationKind.ORDER_STATUS_CHANGED

    def test_guest_order_gets_only_email(self, django_capture_on_commit_callbacks):
        order = GuestOrderFactory(status=OrderStatus.PENDING)

        with patch("apps.notifications.services.send_notification_email") as send:
            with django_capture_on_commit_callbacks(execute=True):
                order.transition_to(OrderStatus.PAID)

        assert Notification.objects.count() == 0
        send.assert_called_once()
        assert send.call_args.kwargs["to"] == order.email

    def test_creating_order_does_not_notify(self, django_capture_on_commit_callbacks):
        with patch("apps.notifications.services.send_notification_email") as send:
            with django_capture_on_commit_callbacks(execute=True):
                OrderFactory(status=OrderStatus.PENDING)

        assert Notification.objects.count() == 0
        send.assert_not_called()


@pytest.mark.django_db
class TestDocumentReadyNotifies:
    def test_issuing_document_notifies_once(self, django_capture_on_commit_callbacks):
        order = OrderFactory(status=OrderStatus.PAID)
        OrderItemFactory(order=order)

        with patch("apps.notifications.services.send_notification_email") as send:
            with django_capture_on_commit_callbacks(execute=True):
                issue_document(order, SalesDocumentKind.CONFIRMATION)

        assert (
            Notification.objects.filter(
                user=order.user, kind=NotificationKind.DOCUMENT_READY
            ).count()
            == 1
        )
        send.assert_called_once()

    def test_reissuing_existing_document_does_not_notify_again(
        self, django_capture_on_commit_callbacks
    ):
        order = OrderFactory(status=OrderStatus.PAID)
        OrderItemFactory(order=order)

        with patch("apps.notifications.services.send_notification_email"):
            with django_capture_on_commit_callbacks(execute=True):
                issue_document(order, SalesDocumentKind.CONFIRMATION)

        with patch("apps.notifications.services.send_notification_email") as send:
            with django_capture_on_commit_callbacks(execute=True):
                issue_document(order, SalesDocumentKind.CONFIRMATION)

        send.assert_not_called()
        assert (
            Notification.objects.filter(kind=NotificationKind.DOCUMENT_READY).count()
            == 1
        )
