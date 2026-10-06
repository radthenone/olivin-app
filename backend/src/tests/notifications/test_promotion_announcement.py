"""Ogłoszenie promocji: e-mail do zgód i subskrypcji bez powtórzeń, push do zgód push (#203)."""

from __future__ import annotations

from typing import Any, cast
from unittest.mock import patch

import pytest

from apps.notifications.models import (
    NewsletterStatus,
    NewsletterSubscription,
    NotificationPreference,
)
from apps.notifications.tasks import announce_promotion
from tests.factories.accounts import UserFactory
from tests.factories.promotions import PromotionFactory

MAIL = "apps.notifications.newsletter.send_notification_email"
PUSH = "apps.notifications.tasks.send_push_notification"


def _announce(promotion) -> tuple[Any, Any]:
    with patch(MAIL) as mail, patch(PUSH) as push:
        cast(Any, announce_promotion)(promotion_id=str(promotion.pk))
    return mail, push


def _recipients(mail) -> list[str]:
    return sorted(call.kwargs["to"] for call in mail.call_args_list)


@pytest.mark.django_db
class TestAnnouncePromotion:
    def test_emails_consenting_accounts_and_active_subscriptions_only(self):
        consenting = UserFactory(email="yes@test.com")
        NotificationPreference.objects.create(user=consenting, marketing_email=True)
        UserFactory(email="no@test.com")
        NewsletterSubscription.objects.create(
            email="sub@test.com", status=NewsletterStatus.ACTIVE
        )
        NewsletterSubscription.objects.create(email="pending@test.com")
        NewsletterSubscription.objects.create(
            email="gone@test.com", status=NewsletterStatus.UNSUBSCRIBED
        )

        mail, _ = _announce(PromotionFactory(name="Jesień"))

        assert _recipients(mail) == ["sub@test.com", "yes@test.com"]
        assert "Jesień" in mail.call_args.kwargs["subject"]

    def test_deduplicates_by_address_case_insensitively(self):
        user = UserFactory(email="Both@test.com")
        NotificationPreference.objects.create(user=user, marketing_email=True)
        NewsletterSubscription.objects.create(
            email="both@test.com", status=NewsletterStatus.ACTIVE
        )

        mail, _ = _announce(PromotionFactory())

        mail.assert_called_once()

    def test_every_email_has_unsubscribe_link(self, settings):
        settings.NEWSLETTER_UNSUBSCRIBE_URL = "https://shop.test/unsub/{token}"
        user = UserFactory(email="yes@test.com")
        NotificationPreference.objects.create(user=user, marketing_email=True)
        subscription = NewsletterSubscription.objects.create(
            email="sub@test.com", status=NewsletterStatus.ACTIVE
        )

        mail, _ = _announce(PromotionFactory())

        bodies = {c.kwargs["to"]: c.kwargs["body"] for c in mail.call_args_list}
        assert f"https://shop.test/unsub/{subscription.unsubscribe_token}" in (
            bodies["sub@test.com"]
        )
        assert "https://shop.test/unsub/" in bodies["yes@test.com"]

    def test_account_unsubscribe_link_turns_off_marketing_email(self, settings):
        from apps.notifications import newsletter

        settings.NEWSLETTER_UNSUBSCRIBE_URL = "https://shop.test/unsub/{token}"
        user = UserFactory(email="yes@test.com")
        NotificationPreference.objects.create(user=user, marketing_email=True)

        mail, _ = _announce(PromotionFactory())

        token = mail.call_args.kwargs["body"].split("https://shop.test/unsub/")[1]
        assert newsletter.unsubscribe(token.split()[0]) is True
        assert NotificationPreference.for_user(user).marketing_email is False

    def test_inactive_account_gets_nothing(self):
        user = UserFactory(email="off@test.com", is_active=False)
        NotificationPreference.objects.create(
            user=user, marketing_email=True, marketing_push=True
        )

        mail, push = _announce(PromotionFactory())

        mail.assert_not_called()
        push.delay.assert_not_called()

    def test_push_goes_only_to_push_consents(self):
        pushy = UserFactory()
        NotificationPreference.objects.create(user=pushy, marketing_push=True)
        mail_only = UserFactory()
        NotificationPreference.objects.create(user=mail_only, marketing_email=True)

        _, push = _announce(PromotionFactory())

        push.delay.assert_called_once()
        assert push.delay.call_args.kwargs["user_id"] == str(pushy.pk)
