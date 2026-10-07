"""Newsletter: double opt-in, wypis bez logowania, przejście na konto (#203)."""

from __future__ import annotations

import base64
import datetime
from unittest.mock import patch

import pytest
from allauth.account.models import EmailAddress
from allauth.account.signals import email_confirmed
from django.core.cache import cache

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
    """Bieżący dokument zgody marketingowej."""
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
    """Model zapisu na newsletter."""

    def test_new_subscription_is_pending_with_distinct_tokens(self):
        """Nowy zapis czeka na potwierdzenie i ma różne tokeny."""
        subscription = NewsletterSubscription.objects.create(email="a@test.com")

        assert subscription.status == NewsletterStatus.PENDING
        assert subscription.confirmed_at is None
        assert subscription.confirmation_token != subscription.unsubscribe_token


@pytest.mark.django_db
class TestSubscribe:
    """Zapis na newsletter z podwójnym potwierdzeniem."""

    def test_creates_pending_subscription_and_sends_confirmation_link(
        self, marketing_document, subscribe
    ):
        """Zapis zakłada oczekujący wpis i wysyła link potwierdzający."""
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
        """Zapis zapamiętuje zgodę gościa na bieżący dokument marketingowy."""
        subscribe("new@test.com")

        consent = Consent.objects.get()
        assert consent.user is None
        assert consent.email == "new@test.com"
        assert consent.document == marketing_document

    def test_without_current_marketing_document_raises_and_saves_nothing(
        self, subscribe
    ):
        """Bez bieżącego dokumentu marketingowego zapis kończy się błędem i nic nie zapisuje."""
        with pytest.raises(newsletter.NoMarketingDocumentError):
            subscribe("new@test.com")

        assert not NewsletterSubscription.objects.exists()
        assert not Consent.objects.exists()

    def test_pending_resubscribe_after_cooldown_resends_without_duplicate(
        self, marketing_document, subscribe
    ):
        """Ponowny zapis po karencji wysyła link jeszcze raz, bez duplikatu."""
        subscribe("new@test.com")
        cache.clear()  # minął cooldown ponownej wysyłki

        send = subscribe("NEW@test.com")

        assert NewsletterSubscription.objects.count() == 1
        assert Consent.objects.count() == 1
        send.assert_called_once()

    def test_pending_resubscribe_records_consent_on_new_document_version(
        self, marketing_document, subscribe
    ):
        """Ponowny zapis zapamiętuje zgodę na nową wersję dokumentu."""
        subscribe("new@test.com")
        newer = ConsentDocumentFactory(
            kind=ConsentKind.MARKETING,
            version="2026-06",
            effective_from=datetime.date(2026, 6, 1),
        )

        subscribe("new@test.com")

        assert set(Consent.objects.values_list("document", flat=True)) == {
            marketing_document.pk,
            newer.pk,
        }

    def test_resubscribe_within_cooldown_sends_no_second_email(
        self, marketing_document, subscribe
    ):
        """Ochrona przed zasypaniem cudzej skrzynki linkami potwierdzenia."""
        subscribe("new@test.com")

        send = subscribe("new@test.com")

        send.assert_not_called()

    def test_active_resubscribe_sends_nothing(self, marketing_document, subscribe):
        """Ponowny zapis aktywnego adresu niczego nie wysyła."""
        NewsletterSubscription.objects.create(
            email="new@test.com", status=NewsletterStatus.ACTIVE
        )

        send = subscribe("new@test.com")

        send.assert_not_called()
        assert NewsletterSubscription.objects.get().status == NewsletterStatus.ACTIVE

    def test_resubscribe_after_unsubscribe_starts_double_opt_in_again(
        self, marketing_document, subscribe
    ):
        """Zapis po wypisaniu zaczyna podwójne potwierdzenie od nowa."""
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
    """Potwierdzenie zapisu linkiem z e-maila."""

    def test_activates_pending_subscription(self):
        """Potwierdzenie aktywuje oczekujący zapis."""
        subscription = NewsletterSubscription.objects.create(email="a@test.com")

        assert newsletter.confirm(str(subscription.confirmation_token)) is True

        subscription.refresh_from_db()
        assert subscription.status == NewsletterStatus.ACTIVE
        assert subscription.confirmed_at is not None

    def test_unknown_or_malformed_token_returns_false(self):
        """Nieznany albo uszkodzony token daje `False`."""
        assert newsletter.confirm("00000000-0000-0000-0000-000000000000") is False
        assert newsletter.confirm("not-a-token") is False

    def test_unsubscribed_subscription_cannot_be_confirmed_with_old_link(self):
        """Wypisanego zapisu nie da się potwierdzić starym linkiem."""
        subscription = NewsletterSubscription.objects.create(
            email="a@test.com", status=NewsletterStatus.UNSUBSCRIBED
        )

        assert newsletter.confirm(str(subscription.confirmation_token)) is False


@pytest.mark.django_db
class TestUnsubscribe:
    """Wypisanie z newslettera."""

    def test_subscription_token_unsubscribes(self):
        """Token zapisu wypisuje z newslettera."""
        subscription = NewsletterSubscription.objects.create(
            email="a@test.com", status=NewsletterStatus.ACTIVE
        )

        assert newsletter.unsubscribe(str(subscription.unsubscribe_token)) is True

        subscription.refresh_from_db()
        assert subscription.status == NewsletterStatus.UNSUBSCRIBED

    def test_account_token_turns_off_marketing_email(self):
        """Token konta wyłącza e-maile marketingowe."""
        user = UserFactory(email="client@test.com")
        NotificationPreference.objects.create(user=user, marketing_email=True)

        token = newsletter.account_unsubscribe_token(user.pk)

        assert newsletter.unsubscribe(token) is True
        assert NotificationPreference.for_user(user).marketing_email is False

    def test_account_token_also_unsubscribes_subscription_on_account_address(self):
        """Token konta wypisuje też zapis na adres konta."""
        user = UserFactory(email="client@test.com")
        NewsletterSubscription.objects.create(
            email="client@test.com", status=NewsletterStatus.ACTIVE
        )

        assert newsletter.unsubscribe(newsletter.account_unsubscribe_token(user.pk))

        assert NewsletterSubscription.objects.get().status == (
            NewsletterStatus.UNSUBSCRIBED
        )

    def test_account_token_does_not_carry_email_address(self):
        """Link trafia do logów serwerów i proxy — bez adresu e-mail (PII)."""
        user = UserFactory(email="client@test.com")

        token = newsletter.account_unsubscribe_token(user.pk)

        payload = base64.urlsafe_b64decode(token.split(":")[0] + "==")
        assert b"client" not in payload

    def test_unknown_token_returns_false(self):
        """Nieznany token daje `False`."""
        assert newsletter.unsubscribe("00000000-0000-0000-0000-000000000000") is False
        assert newsletter.unsubscribe("garbage") is False


def _confirm_account_email(user, email: str | None = None) -> None:
    address = EmailAddress.objects.create(
        user=user, email=email or user.email, verified=True, primary=True
    )
    email_confirmed.send(sender=EmailAddress, request=None, email_address=address)


@pytest.mark.django_db
class TestTransferToAccount:
    """Przejście na konto dopiero po potwierdzeniu adresu konta — jak zamówienia gościa.

    Samo założenie konta na cudzy adres nie może przejąć subskrypcji: konto
    niepotwierdzone jest potem sprzątane, a subskrypcja przepadłaby razem z nim.
    """

    def test_confirmed_account_email_moves_active_subscription_to_preference(self):
        """Potwierdzony adres konta przenosi aktywny zapis do preferencji."""
        NewsletterSubscription.objects.create(
            email="client@test.com", status=NewsletterStatus.ACTIVE
        )
        user = UserFactory(email="Client@test.com")

        _confirm_account_email(user)

        assert NotificationPreference.for_user(user).marketing_email is True
        assert not NewsletterSubscription.objects.exists()

    def test_unconfirmed_account_does_not_take_subscription(self):
        """Niepotwierdzone konto nie przejmuje zapisu."""
        NewsletterSubscription.objects.create(
            email="client@test.com", status=NewsletterStatus.ACTIVE
        )

        user = UserFactory(email="client@test.com")

        assert NotificationPreference.for_user(user).marketing_email is False
        assert NewsletterSubscription.objects.filter(
            status=NewsletterStatus.ACTIVE
        ).exists()

    def test_pending_subscription_is_not_moved_on_email_confirmation(self):
        """Oczekujący zapis nie przechodzi na konto przy potwierdzeniu adresu."""
        NewsletterSubscription.objects.create(email="client@test.com")
        user = UserFactory(email="client@test.com")

        _confirm_account_email(user)

        assert NotificationPreference.for_user(user).marketing_email is False
        assert NewsletterSubscription.objects.filter(
            status=NewsletterStatus.PENDING
        ).exists()

    def test_confirming_subscription_of_verified_account_moves_to_preference(self):
        """Potwierdzenie zapisu zweryfikowanego konta przenosi go do preferencji."""
        subscription = NewsletterSubscription.objects.create(email="client@test.com")
        user = UserFactory(email="client@test.com")
        _confirm_account_email(user)

        assert newsletter.confirm(str(subscription.confirmation_token)) is True

        assert NotificationPreference.for_user(user).marketing_email is True
        assert not NewsletterSubscription.objects.exists()

    def test_confirming_subscription_of_unverified_account_keeps_subscription(self):
        """Potwierdzenie zapisu niezweryfikowanego konta zostawia zapis."""
        subscription = NewsletterSubscription.objects.create(email="client@test.com")
        user = UserFactory(email="client@test.com")

        assert newsletter.confirm(str(subscription.confirmation_token)) is True

        assert NotificationPreference.for_user(user).marketing_email is False
        assert NewsletterSubscription.objects.get().status == NewsletterStatus.ACTIVE
