"""Newsletter: double opt-in, wypis bez logowania, przejście na konto (#203)."""

from __future__ import annotations

import datetime
from unittest.mock import patch

import pytest

from apps.consents.models import Consent, ConsentKind
from apps.notifications import newsletter
from apps.notifications.models import (
    NewsletterStatus,
    NewsletterSubscription,
    NotificationPreference,
)
from tests.factories.accounts import UserFactory
from tests.factories.consents import ConsentDocumentFactory

MAIL = "apps.notifications.newsletter.send_notification_email"


@pytest.fixture
def marketing_document():
    return ConsentDocumentFactory(
        kind=ConsentKind.MARKETING,
        version="2026-01",
        effective_from=datetime.date(2026, 1, 1),
    )


@pytest.fixture
def subscribe(django_capture_on_commit_callbacks):
    """Zapis z przechwyconą wysyłką po commicie; zwraca atrapę maila."""

    def _subscribe(email: str):
        with patch(MAIL) as send:
            with django_capture_on_commit_callbacks(execute=True):
                newsletter.subscribe(email)
        return send

    return _subscribe


@pytest.mark.django_db
class TestNewsletterSubscriptionModel:
    def test_new_subscription_is_pending_with_distinct_tokens(self):
        subscription = NewsletterSubscription.objects.create(email="a@test.com")

        assert subscription.status == NewsletterStatus.PENDING
        assert subscription.confirmed_at is None
        assert subscription.confirmation_token != subscription.unsubscribe_token


@pytest.mark.django_db
class TestSubscribe:
    def test_creates_pending_subscription_and_sends_confirmation_link(
        self, marketing_document, subscribe
    ):
        send = subscribe("  New@Test.com ")

        subscription = NewsletterSubscription.objects.get()
        assert subscription.email == "new@test.com"
        assert subscription.status == NewsletterStatus.PENDING
        send.assert_called_once()
        assert send.call_args.kwargs["to"] == "new@test.com"
        assert str(subscription.confirmation_token) in send.call_args.kwargs["body"]

    def test_records_guest_consent_on_current_marketing_document(
        self, marketing_document, subscribe
    ):
        subscribe("new@test.com")

        consent = Consent.objects.get()
        assert consent.user is None
        assert consent.email == "new@test.com"
        assert consent.document == marketing_document

    def test_without_current_marketing_document_raises_and_saves_nothing(
        self, subscribe
    ):
        with pytest.raises(newsletter.NoMarketingDocumentError):
            subscribe("new@test.com")

        assert not NewsletterSubscription.objects.exists()
        assert not Consent.objects.exists()

    def test_pending_resubscribe_resends_without_duplicate(
        self, marketing_document, subscribe
    ):
        subscribe("new@test.com")
        send = subscribe("NEW@test.com")

        assert NewsletterSubscription.objects.count() == 1
        assert Consent.objects.count() == 1
        send.assert_called_once()

    def test_active_resubscribe_sends_nothing(self, marketing_document, subscribe):
        NewsletterSubscription.objects.create(
            email="new@test.com", status=NewsletterStatus.ACTIVE
        )

        send = subscribe("new@test.com")

        send.assert_not_called()
        assert NewsletterSubscription.objects.get().status == NewsletterStatus.ACTIVE

    def test_resubscribe_after_unsubscribe_starts_double_opt_in_again(
        self, marketing_document, subscribe
    ):
        old = NewsletterSubscription.objects.create(
            email="new@test.com", status=NewsletterStatus.UNSUBSCRIBED
        )

        send = subscribe("new@test.com")

        subscription = NewsletterSubscription.objects.get()
        assert subscription.status == NewsletterStatus.PENDING
        assert subscription.confirmation_token != old.confirmation_token
        assert Consent.objects.count() == 1
        send.assert_called_once()


@pytest.mark.django_db
class TestConfirm:
    def test_activates_pending_subscription(self):
        subscription = NewsletterSubscription.objects.create(email="a@test.com")

        assert newsletter.confirm(str(subscription.confirmation_token)) is True

        subscription.refresh_from_db()
        assert subscription.status == NewsletterStatus.ACTIVE
        assert subscription.confirmed_at is not None

    def test_unknown_or_malformed_token_returns_false(self):
        assert newsletter.confirm("00000000-0000-0000-0000-000000000000") is False
        assert newsletter.confirm("not-a-token") is False

    def test_unsubscribed_subscription_cannot_be_confirmed_with_old_link(self):
        subscription = NewsletterSubscription.objects.create(
            email="a@test.com", status=NewsletterStatus.UNSUBSCRIBED
        )

        assert newsletter.confirm(str(subscription.confirmation_token)) is False


@pytest.mark.django_db
class TestUnsubscribe:
    def test_subscription_token_unsubscribes(self):
        subscription = NewsletterSubscription.objects.create(
            email="a@test.com", status=NewsletterStatus.ACTIVE
        )

        assert newsletter.unsubscribe(str(subscription.unsubscribe_token)) is True

        subscription.refresh_from_db()
        assert subscription.status == NewsletterStatus.UNSUBSCRIBED

    def test_account_token_turns_off_marketing_email(self):
        user = UserFactory(email="client@test.com")
        NotificationPreference.objects.create(user=user, marketing_email=True)

        token = newsletter.account_unsubscribe_token("Client@test.com")

        assert newsletter.unsubscribe(token) is True
        assert NotificationPreference.for_user(user).marketing_email is False

    def test_unknown_token_returns_false(self):
        assert newsletter.unsubscribe("00000000-0000-0000-0000-000000000000") is False
        assert newsletter.unsubscribe("garbage") is False
