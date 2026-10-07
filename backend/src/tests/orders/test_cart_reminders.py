"""Przypomnienie o koszyku (`CONTEXT.md`, CartReminder, #208)."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from django.utils import timezone
from freezegun import freeze_time

from apps.consents.models import ConsentKind
from apps.notifications.newsletter import account_unsubscribe_url
from apps.orders.models import OrderStatus
from apps.orders.services import ShippingAddress, create_order
from apps.orders.services.cart_reminder import due_carts
from tests.factories.consents import ConsentDocumentFactory, ConsentFactory
from tests.factories.shipping import ShippingMethodFactory

from apps.notifications.models import (
    Notification,
    NotificationKind,
    NotificationPreference,
    PushDevice,
)
from apps.orders.models import Cart
from apps.products.models import ProductStatus
from apps.orders.services.cart import add_item, cart_items
from apps.orders.services.cart_reminder import send_cart_reminders
from apps.orders.tasks import send_cart_reminders as send_cart_reminders_task
from core.integrations.push.fake import FakePushProvider
from tests.factories.accounts import UserFactory
from tests.factories.orders import (
    CartFactory,
    CartItemFactory,
    GuestCartFactory,
)
from tests.factories.products import (
    MadeToOrderProductFactory,
    ProductVariantFactory,
    PublishedProductFactory,
)

START = "2026-10-01 10:00:00"
ADDRESS = ShippingAddress(
    recipient_name="Jan Kowalski",
    street="Złota 44",
    city="Warszawa",
    postal_code="00-120",
    country="PL",
)


@pytest.fixture
def push_provider(settings):
    settings.PUSH_PROVIDER = "core.integrations.push.fake.FakePushProvider"
    FakePushProvider.reset()
    yield FakePushProvider
    FakePushProvider.reset()


def _device(cart):
    PushDevice.objects.create(
        user=cart.user, token=f"ExponentPushToken[{cart.pk}]", platform="ios"
    )


@pytest.fixture
def mail():
    with patch("apps.notifications.services.send_notification_email") as sent:
        yield sent


def _available_variant(**kwargs):
    return ProductVariantFactory(product=MadeToOrderProductFactory(), **kwargs)


def _sold_out_variant():
    # Wyrób magazynowy bez stanu — `is_available` = False.
    return ProductVariantFactory(product=PublishedProductFactory())


def _consenting_cart(*, email=True, push=False, variants=None, active=True):
    user = UserFactory(is_active=active)
    NotificationPreference.objects.create(
        user=user, marketing_email=email, marketing_push=push
    )
    cart = CartFactory(user=user)
    for variant in variants if variants is not None else [_available_variant()]:
        CartItemFactory(cart=cart, variant=variant)
    return cart


def _run(django_capture_on_commit_callbacks) -> int:
    with django_capture_on_commit_callbacks(execute=True):
        return send_cart_reminders()


@pytest.mark.django_db
class TestCartReminderSelection:
    def test_sent_after_24_hours_of_inactivity(
        self, mail, django_capture_on_commit_callbacks
    ):
        with freeze_time(START):
            cart = _consenting_cart()
        with freeze_time("2026-10-02 10:01:00"):
            assert _run(django_capture_on_commit_callbacks) == 1

        assert mail.call_count == 1
        assert cart.user is not None
        assert mail.call_args.kwargs["to"] == cart.user.email
        cart.refresh_from_db()
        assert cart.reminded_at is not None
        assert Notification.objects.filter(
            user=cart.user, kind=NotificationKind.CART_REMINDER
        ).exists()

    def test_not_sent_before_24_hours(self, mail, django_capture_on_commit_callbacks):
        with freeze_time(START):
            _consenting_cart()
        with freeze_time("2026-10-02 09:59:00"):
            assert _run(django_capture_on_commit_callbacks) == 0

        mail.assert_not_called()

    def test_not_sent_without_marketing_email_consent(
        self, mail, django_capture_on_commit_callbacks
    ):
        with freeze_time(START):
            cart = _consenting_cart(email=False)
        with freeze_time("2026-10-03 10:00:00"):
            assert _run(django_capture_on_commit_callbacks) == 0

        mail.assert_not_called()
        cart.refresh_from_db()
        assert cart.reminded_at is None

    def test_guest_never_gets_reminder(self, mail, django_capture_on_commit_callbacks):
        with freeze_time(START):
            CartItemFactory(cart=GuestCartFactory(), variant=_available_variant())
        with freeze_time("2026-10-03 10:00:00"):
            assert _run(django_capture_on_commit_callbacks) == 0

        mail.assert_not_called()

    def test_empty_cart_gets_no_reminder(
        self, mail, django_capture_on_commit_callbacks
    ):
        with freeze_time(START):
            _consenting_cart(variants=[])
        with freeze_time("2026-10-03 10:00:00"):
            assert _run(django_capture_on_commit_callbacks) == 0

    def test_inactive_account_gets_no_reminder(
        self, mail, django_capture_on_commit_callbacks
    ):
        with freeze_time(START):
            _consenting_cart(active=False)
        with freeze_time("2026-10-03 10:00:00"):
            assert _run(django_capture_on_commit_callbacks) == 0

    def test_not_repeated_without_content_change(
        self, mail, django_capture_on_commit_callbacks
    ):
        with freeze_time(START):
            _consenting_cart()
        with freeze_time("2026-10-02 11:00:00"):
            assert _run(django_capture_on_commit_callbacks) == 1
        with freeze_time("2026-10-05 11:00:00"):
            assert _run(django_capture_on_commit_callbacks) == 0

        assert mail.call_count == 1

    def test_repeated_after_content_change_and_next_24_hours(
        self, mail, django_capture_on_commit_callbacks
    ):
        with freeze_time(START):
            cart = _consenting_cart()
        with freeze_time("2026-10-02 11:00:00"):
            assert _run(django_capture_on_commit_callbacks) == 1
        with freeze_time("2026-10-03 12:00:00"):
            add_item(cart, variant=_available_variant())
        with freeze_time("2026-10-04 11:00:00"):
            assert _run(django_capture_on_commit_callbacks) == 0
        with freeze_time("2026-10-04 12:01:00"):
            assert _run(django_capture_on_commit_callbacks) == 1

        assert mail.call_count == 2

    def test_only_unavailable_items_send_nothing(
        self, mail, django_capture_on_commit_callbacks
    ):
        with freeze_time(START):
            cart = _consenting_cart(
                variants=[_sold_out_variant(), ProductVariantFactory()]
            )
        with freeze_time("2026-10-03 10:00:00"):
            assert _run(django_capture_on_commit_callbacks) == 0

        mail.assert_not_called()
        cart.refresh_from_db()
        assert cart.reminded_at is None

    def test_pending_order_does_not_trigger_reminder(
        self, mail, settings, django_capture_on_commit_callbacks
    ):
        """Złożone, nieopłacone zamówienie nie jest porzuconym koszykiem."""
        settings.FREE_SHIPPING_THRESHOLD = None
        with freeze_time(START):
            cart = _consenting_cart()
            assert cart.user is not None
            ConsentFactory(
                user=cart.user,
                document=ConsentDocumentFactory(kind=ConsentKind.TERMS),
            )
            order = create_order(
                cart=cart,
                address=ADDRESS,
                shipping_method=ShippingMethodFactory(rate=1990),
                user=cart.user,
            )
        assert order.status == OrderStatus.PENDING
        with freeze_time("2026-10-03 10:00:00"):
            assert _run(django_capture_on_commit_callbacks) == 0

        mail.assert_not_called()

    def test_push_only_consent_gets_push_reminder(
        self, mail, push_provider, django_capture_on_commit_callbacks
    ):
        """Zgoda „na danym kanale” (`CONTEXT.md`, CartReminder) — sam push też wystarcza."""
        with freeze_time(START):
            cart = _consenting_cart(email=False, push=True)
            _device(cart)
        with freeze_time("2026-10-03 10:00:00"):
            assert _run(django_capture_on_commit_callbacks) == 1

        mail.assert_not_called()
        assert len(push_provider.sent) == 1
        cart.refresh_from_db()
        assert cart.reminded_at is not None

    def test_sold_out_cart_is_not_selected(self):
        with freeze_time(START):
            _consenting_cart(variants=[_sold_out_variant()])
        with freeze_time("2026-10-03 10:00:00"):
            assert not due_carts(timezone.now()).exists()


@pytest.mark.django_db
class TestCartReminderContent:
    def test_lists_items_with_price_and_marks_unavailable(
        self, mail, settings, django_capture_on_commit_callbacks
    ):
        settings.CART_URL = "https://shop.test/cart"
        settings.NOTIFICATION_PREFERENCES_URL = (
            "https://shop.test/account/notifications"
        )
        available = _available_variant(sku="AV-1")
        sold_out = ProductVariantFactory(product=PublishedProductFactory(), sku="SO-1")
        draft = ProductVariantFactory(
            product=MadeToOrderProductFactory(status=ProductStatus.DRAFT), sku="DR-1"
        )
        with freeze_time(START):
            cart = _consenting_cart(variants=[available, sold_out, draft])
        with freeze_time("2026-10-03 10:00:00"):
            _run(django_capture_on_commit_callbacks)

        body = mail.call_args.kwargs["body"]
        lines = {item.variant.sku: item for item in cart_items(cart)}
        assert str(lines["AV-1"].line_total) in body
        assert "niedostępn" not in _line(body, "AV-1")
        assert "niedostępn" in _line(body, "SO-1")
        assert "niedostępn" in _line(body, "DR-1")
        assert "https://shop.test/cart" in body
        assert "https://shop.test/account/notifications" in body

    def test_push_is_short_with_type_data(
        self, mail, push_provider, django_capture_on_commit_callbacks
    ):
        variant = _available_variant(sku="AV-PUSH")
        with freeze_time(START):
            cart = _consenting_cart(push=True, variants=[variant])
            _device(cart)
        with freeze_time("2026-10-03 10:00:00"):
            _run(django_capture_on_commit_callbacks)

        assert len(push_provider.sent) == 1
        sent = push_provider.sent[0]
        assert "AV-PUSH" not in sent["body"]
        assert "1" in sent["body"]
        assert sent["data"] == {"type": "cart_reminder"}

    def test_email_has_one_click_unsubscribe_link(
        self, mail, settings, django_capture_on_commit_callbacks
    ):
        settings.NEWSLETTER_UNSUBSCRIBE_URL = "https://shop.test/unsubscribe/{token}"
        with freeze_time(START):
            cart = _consenting_cart()
        assert cart.user is not None
        with freeze_time("2026-10-03 10:00:00"):
            _run(django_capture_on_commit_callbacks)
            expected = account_unsubscribe_url(cart.user.pk)

        assert f"Wypisz się: {expected}" in mail.call_args.kwargs["body"]


@pytest.mark.django_db
def test_periodic_task_runs_service(mail, django_capture_on_commit_callbacks):
    with freeze_time(START):
        _consenting_cart()
    with freeze_time("2026-10-03 10:00:00"):
        with django_capture_on_commit_callbacks(execute=True):
            assert send_cart_reminders_task() == 1  # type: ignore[missing-argument]
    assert Cart.objects.filter(reminded_at__isnull=False).count() == 1


def _line(body: str, sku: str) -> str:
    return next(line for line in body.splitlines() if sku in line)
