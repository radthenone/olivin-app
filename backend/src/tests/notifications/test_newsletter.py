"""Newsletter: double opt-in, wypis bez logowania, przejście na konto (#203)."""

from __future__ import annotations

import pytest

from apps.notifications.models import NewsletterStatus, NewsletterSubscription


@pytest.mark.django_db
class TestNewsletterSubscriptionModel:
    def test_new_subscription_is_pending_with_distinct_tokens(self):
        subscription = NewsletterSubscription.objects.create(email="a@test.com")

        assert subscription.status == NewsletterStatus.PENDING
        assert subscription.confirmed_at is None
        assert subscription.confirmation_token != subscription.unsubscribe_token
