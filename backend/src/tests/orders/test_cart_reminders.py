"""Przypomnienie o koszyku (`CONTEXT.md`, CartReminder, #208)."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from freezegun import freeze_time

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
    OrderFactory,
)
from tests.factories.products import (
    MadeToOrderProductFactory,
    ProductVariantFactory,
    PublishedProductFactory,
)

START = "2026-10-01 10:00:00"


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
        self, mail, django_capture_on_commit_callbacks
    ):
        """Złożone zamówienie opróżnia koszyk — nieopłacone nie jest porzuconym koszykiem."""
        with freeze_time(START):
            cart = _consenting_cart(variants=[])
            OrderFactory(user=cart.user)
        with freeze_time("2026-10-03 10:00:00"):
            assert _run(django_capture_on_commit_callbacks) == 0

        mail.assert_not_called()


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

    def test_push_sent_with_marketing_push_and_device(
        self, mail, settings, django_capture_on_commit_callbacks
    ):
        settings.PUSH_PROVIDER = "core.integrations.push.fake.FakePushProvider"
        FakePushProvider.reset()
        with freeze_time(START):
            cart = _consenting_cart(push=True)
            PushDevice.objects.create(
                user=cart.user, token="ExponentPushToken[x]", platform="ios"
            )
        with freeze_time("2026-10-03 10:00:00"):
            _run(django_capture_on_commit_callbacks)

        assert len(FakePushProvider.sent) == 1
        FakePushProvider.reset()


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
