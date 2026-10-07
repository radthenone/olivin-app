"""Anonimizacja konta (#204, ADR 0029): blokada i zakres wymazania."""

from __future__ import annotations

import datetime
import logging

import pytest
from allauth.account.models import EmailAddress
from allauth.mfa.models import Authenticator
from allauth.socialaccount.models import SocialAccount
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.sessions.models import Session

from apps.accounts.models import Address, CustomUser, Profile
from apps.accounts.services.anonymisation_service import (
    ActiveOrderError,
    StaffAccountError,
    anonymise_account,
)
from apps.consents.models import Consent
from apps.favorites.models import Favorite
from apps.notifications.models import (
    NewsletterStatus,
    NewsletterSubscription,
    NotificationPreference,
    PushDevice,
    PushPlatform,
)
from apps.orders.models import Cart, Order, OrderStatus
from apps.reviews.models import Review
from apps.watches.models import Watch
from tests.factories.accounts import AdminUserFactory, ProfileFactory, UserFactory
from tests.factories.consents import ConsentFactory
from tests.factories.favorites import FavoriteFactory
from tests.factories.orders import CartFactory, OrderFactory
from tests.factories.reviews import ReviewFactory
from tests.factories.watches import WatchFactory

pytestmark = pytest.mark.django_db

EMAIL = "jan.kowalski@test.com"


@pytest.fixture
def customer() -> CustomUser:
    user = UserFactory(email=EMAIL, first_name="Jan", last_name="Kowalski")
    profile = ProfileFactory(
        user=user,
        first_name="Jan",
        last_name="Kowalski",
        date_of_birth=datetime.date(1990, 5, 17),
        phone_number="+48600100200",
    )
    Address.objects.create(profile=profile, street="Złota 44", city="Warszawa")
    return user


@pytest.mark.parametrize(
    "order_status",
    [
        OrderStatus.PENDING,
        OrderStatus.PAID,
        OrderStatus.IN_PRODUCTION,
        OrderStatus.PACKED,
        OrderStatus.SHIPPED,
    ],
)
def test_refuses_while_order_is_not_finished(customer, order_status) -> None:
    OrderFactory(user=customer, status=order_status)

    with pytest.raises(ActiveOrderError):
        anonymise_account(customer)

    customer.refresh_from_db()
    assert customer.email == EMAIL
    assert customer.is_active


@pytest.mark.parametrize(
    "order_status",
    [OrderStatus.DELIVERED, OrderStatus.CANCELLED, OrderStatus.RETURNED],
)
def test_finished_orders_do_not_block(customer, order_status) -> None:
    OrderFactory(user=customer, status=order_status)

    anonymise_account(customer)

    customer.refresh_from_db()
    assert not customer.is_active


def test_erases_personal_data_of_account_and_profile(customer) -> None:
    old_username = customer.username

    anonymise_account(customer)

    customer.refresh_from_db()
    assert customer.email.endswith("@anonymised.invalid")
    assert EMAIL.split("@")[0] not in customer.email
    assert customer.first_name == customer.last_name == ""
    assert customer.username.startswith("anon")
    assert customer.username != old_username
    assert not customer.is_active
    assert not customer.has_usable_password()
    profile = Profile.objects.get(user=customer)
    assert profile.first_name == profile.last_name == ""
    assert profile.date_of_birth is None
    assert str(profile.phone_number) == ""
    assert not Address.objects.filter(profile=profile).exists()


def test_technical_email_is_unique_per_account(customer) -> None:
    other = UserFactory()

    anonymise_account(customer)
    anonymise_account(other)

    customer.refresh_from_db()
    other.refresh_from_db()
    assert customer.email != other.email


def test_erases_logins_social_accounts_mfa_and_sessions(customer) -> None:
    EmailAddress.objects.create(user=customer, email=EMAIL, verified=True, primary=True)
    SocialAccount.objects.create(user=customer, provider="google", uid="g-1")
    Authenticator.objects.create(
        user=customer, type=Authenticator.Type.RECOVERY_CODES, data={}
    )
    session = SessionStore()
    session["_auth_user_id"] = str(customer.pk)
    session.create()
    foreign = SessionStore()
    foreign["_auth_user_id"] = str(UserFactory().pk)
    foreign.create()

    anonymise_account(customer)

    assert not EmailAddress.objects.filter(user=customer).exists()
    assert not SocialAccount.objects.filter(user=customer).exists()
    assert not Authenticator.objects.filter(user=customer).exists()
    assert not Session.objects.filter(session_key=session.session_key).exists()
    assert Session.objects.filter(session_key=foreign.session_key).exists()


def test_deletes_lists_devices_and_preferences(customer) -> None:
    FavoriteFactory(user=customer)
    WatchFactory(user=customer)
    CartFactory(user=customer)
    PushDevice.objects.create(
        user=customer, token="ExponentPushToken[a]", platform=PushPlatform.IOS
    )
    NotificationPreference.objects.create(user=customer, marketing_email=True)
    others_favorite = FavoriteFactory()
    others_watch = WatchFactory()

    anonymise_account(customer)

    assert not Favorite.objects.filter(user=customer).exists()
    assert not Watch.objects.filter(user=customer).exists()
    assert not Cart.objects.filter(user=customer).exists()
    assert not PushDevice.objects.filter(user=customer).exists()
    assert not NotificationPreference.objects.filter(user=customer).exists()
    assert Favorite.objects.filter(pk=others_favorite.pk).exists()
    assert Watch.objects.filter(pk=others_watch.pk).exists()


def test_unsubscribes_newsletter_of_account_address(customer) -> None:
    subscription = NewsletterSubscription.objects.create(
        email=EMAIL, status=NewsletterStatus.ACTIVE
    )

    anonymise_account(customer)

    subscription.refresh_from_db()
    assert subscription.status == NewsletterStatus.UNSUBSCRIBED


def test_keeps_orders_consents_and_reviews(customer) -> None:
    order = OrderFactory(user=customer, email=EMAIL, status=OrderStatus.DELIVERED)
    consent = ConsentFactory(user=customer)
    review = ReviewFactory(user=customer)

    anonymise_account(customer)

    order = Order.objects.get(pk=order.pk)
    assert order.user == customer
    assert order.email == EMAIL
    assert order.recipient_name == "Jan Kowalski"
    assert Consent.objects.filter(pk=consent.pk, user=customer).exists()
    assert Review.objects.filter(pk=review.pk, user=customer).exists()


def test_logs_without_personal_data(customer, caplog) -> None:
    with caplog.at_level(logging.INFO):
        anonymise_account(customer)

    assert str(customer.pk) in caplog.text
    assert EMAIL not in caplog.text
    assert "Kowalski" not in caplog.text


def test_unsubscribes_newsletter_of_every_account_address(customer) -> None:
    EmailAddress.objects.create(user=customer, email="Second@Test.com", verified=True)
    secondary = NewsletterSubscription.objects.create(
        email="second@test.com", status=NewsletterStatus.ACTIVE
    )
    stranger = NewsletterSubscription.objects.create(
        email="stranger@test.com", status=NewsletterStatus.ACTIVE
    )

    anonymise_account(customer)

    secondary.refresh_from_db()
    stranger.refresh_from_db()
    assert secondary.status == NewsletterStatus.UNSUBSCRIBED
    assert stranger.status == NewsletterStatus.ACTIVE


@pytest.mark.parametrize("staff", [{"is_staff": True}, {"is_superuser": True}])
def test_refuses_staff_accounts(staff) -> None:
    user = UserFactory(**staff)

    with pytest.raises(StaffAccountError):
        anonymise_account(user)

    user.refresh_from_db()
    assert user.is_active


def test_refuses_admin_account() -> None:
    with pytest.raises(StaffAccountError):
        anonymise_account(AdminUserFactory())
