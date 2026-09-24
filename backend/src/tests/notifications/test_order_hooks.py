"""Podpięcie powiadomień: zmiana statusu, `paid`, dokument gotowy (#156)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from apps.consents.models import ConsentKind
from apps.notifications.models import Notification, NotificationKind
from apps.orders.models import OrderStatus, SalesDocumentKind
from apps.orders.services import ShippingAddress, apply_coupon_code, create_order
from apps.orders.services.cart import add_item
from apps.orders.services.document import issue_document
from apps.payments.services import handle_event, start_payment
from apps.products.services.metal_rate import activate_rate
from core.integrations.payments import EventKind, ProviderEvent
from tests.factories.accounts import UserFactory
from tests.factories.consents import ConsentDocumentFactory, ConsentFactory
from tests.factories.orders import (
    CartFactory,
    GuestOrderFactory,
    OrderFactory,
    OrderItemFactory,
)
from tests.factories.products import (
    MetalRateFactory,
    ProductVariantFactory,
    PublishedProductFactory,
    stock,
)
from tests.factories.promotions import CouponFactory
from tests.factories.shipping import ShippingMethodFactory
from tests.payments.helpers import placed_order

ADDRESS = ShippingAddress(
    recipient_name="Jan Kowalski",
    street="Złota 44",
    city="Warszawa",
    postal_code="00-120",
    country="PL",
)


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
        assert send.call_args.kwargs["to"] == order.email

    def test_email_goes_to_order_email_not_stale_user_email(
        self, django_capture_on_commit_callbacks
    ):
        """`order.email` jest kopią z chwili złożenia — liczy się ona, nie
        dzisiejszy e-mail konta, który mógł się zmienić albo zostać
        zanonimizowany (`CONTEXT.md`, Account anonymisation)."""
        order = OrderFactory(status=OrderStatus.PENDING, email="zlozenie@test.com")
        assert order.user is not None
        order.user.email = "inny@test.com"
        order.user.save(update_fields=["email"])

        with patch("apps.notifications.services.send_notification_email") as send:
            with django_capture_on_commit_callbacks(execute=True):
                order.transition_to(OrderStatus.PAID)

        assert send.call_args.kwargs["to"] == "zlozenie@test.com"

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


@pytest.mark.django_db
class TestCouponPaidOrderNotifiesOnce:
    def test_full_coupon_coverage_notifies_exactly_once(
        self, django_capture_on_commit_callbacks
    ):
        """Zamówienie w całości pokryte kuponem trafia w `paid` przy tworzeniu,
        bez operatora płatności (#154) — sygnał ma to zauważyć tak samo jak
        `mark_paid()` wołane z webhooka Stripe (#156)."""
        activate_rate(MetalRateFactory(price_per_gram=10000))
        user = UserFactory()
        ConsentFactory(
            user=user,
            document=ConsentDocumentFactory(kind=ConsentKind.TERMS),
        )
        cart = CartFactory(user=user)
        variant = ProductVariantFactory(product=PublishedProductFactory(), price=30000)
        stock(variant, 5)
        add_item(cart, variant=variant)
        apply_coupon_code(cart, CouponFactory(nominal=50000).code)

        with patch("apps.notifications.services.send_notification_email"):
            with django_capture_on_commit_callbacks(execute=True):
                order = create_order(
                    cart=cart,
                    address=ADDRESS,
                    shipping_method=ShippingMethodFactory(rate=0),
                    user=user,
                )

        assert order.status == OrderStatus.PAID
        assert (
            Notification.objects.filter(
                user=user, kind=NotificationKind.ORDER_PAID
            ).count()
            == 1
        )


@pytest.mark.django_db
class TestWebhookDoesNotDuplicateNotification:
    def test_repeated_payment_event_notifies_once(
        self, django_capture_on_commit_callbacks
    ):
        """Drugie zdarzenie zapłaty (retry operatora) nie dubluje powiadomienia:
        `_settle()` odrzuca je, bo płatność nie jest już `pending`/`failed`."""
        order = placed_order()
        started = start_payment(order)
        event = ProviderEvent(
            id="evt_paid",
            kind=EventKind.PAYMENT_SUCCEEDED,
            type=str(EventKind.PAYMENT_SUCCEEDED),
            intent_id=started.payment.intent_id,
        )

        with patch("apps.notifications.services.send_notification_email"):
            with django_capture_on_commit_callbacks(execute=True):
                handle_event(event)
                handle_event(event)

        assert (
            Notification.objects.filter(
                user=order.user, kind=NotificationKind.ORDER_PAID
            ).count()
            == 1
        )
