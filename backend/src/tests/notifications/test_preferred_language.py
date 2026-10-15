"""Preferowany język klienta: zapis i maile w tym języku (#316, ADR 0035)."""

from __future__ import annotations

import datetime
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

import pytest
from django.conf import settings
from django.test import RequestFactory
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import CustomUser, Profile
from apps.consents.models import ConsentKind
from apps.notifications.models import NewsletterSubscription, NotificationKind
from apps.notifications.services import notify
from apps.orders.models import Order
from apps.orders.services.cart import add_item
from apps.orders.services.cart_reminder import send_cart_reminder
from common.languages import (
    PreferredLanguage,
    email_language,
    language_from_request,
    localized_link,
)
from tests.factories.accounts import ProfileFactory, UserFactory
from tests.factories.consents import ConsentDocumentFactory, GuestConsentFactory
from tests.factories.orders import GuestCartFactory
from tests.factories.products import (
    ProductVariantFactory,
    PublishedProductFactory,
    stock,
)
from tests.factories.shipping import ShippingMethodFactory

NOTIFY_MAIL = "apps.notifications.services.send_notification_email"
NEWSLETTER_MAIL = "apps.notifications.newsletter.send_notification_email"


class TestLanguageFromRequest:
    """`Accept-Language`: `pl*` → `pl`, inny język → `en`, brak → brak wartości."""

    @pytest.mark.parametrize(
        ("header", "expected"),
        [
            ("pl-PL,pl;q=0.9,en;q=0.8", "pl"),
            ("pl", "pl"),
            ("en-GB,en;q=0.9", "en"),
            ("de", "en"),
            ("de;q=0.5,pl;q=0.9", "pl"),
            ("plx", "en"),
            ("pl;q=0,de", "en"),
            ("pl;q=0", None),
            ("", None),
        ],
    )
    def test_maps_header(self, header: str, expected: str | None):
        """Najwyżej ważony język decyduje; pusty nagłówek nie zgaduje."""
        request = RequestFactory().get("/", HTTP_ACCEPT_LANGUAGE=header)

        assert language_from_request(request) == expected


class TestLocalizedLink:
    """Prefiks języka po `FRONTEND_URL` w linkach z maili."""

    def test_swaps_prefix_for_english(self):
        """Link sklepu dostaje `/en/` zamiast `/pl/`."""
        link = localized_link(settings.CART_URL, PreferredLanguage.EN)

        assert link == f"{settings.FRONTEND_URL}/en/cart"

    def test_polish_and_foreign_links_unchanged(self):
        """Polski zostaje bez zmian; obcy adres nie jest ruszany."""
        assert localized_link(settings.CART_URL, "pl") == settings.CART_URL
        assert localized_link("https://other.test/pl/x", "en") == (
            "https://other.test/pl/x"
        )


@pytest.mark.django_db
class TestEmailLanguage:
    """Jeden pomocnik dla konta, zamówienia gościa i subskrypcji."""

    def test_account_uses_profile(self):
        """Konto bierze język z profilu; brak profilu albo wartości → `pl`."""
        english = ProfileFactory(preferred_language=PreferredLanguage.EN).user
        without_profile = UserFactory()

        assert email_language(english) == "en"
        assert email_language(without_profile) == "pl"
        assert email_language(None) == "pl"

    def test_guest_order_and_subscription_use_own_field(self):
        """Zamówienie gościa i subskrypcja mają własne pole."""
        assert email_language(SimpleNamespace(user=None, preferred_language="en")) == (
            "en"
        )
        assert email_language(SimpleNamespace(preferred_language=None)) == "pl"


@pytest.mark.django_db
class TestNotifyInPreferredLanguage:
    """`notify()` renderuje temat i linki w języku odbiorcy."""

    def test_english_account_gets_english_subject(
        self, django_capture_on_commit_callbacks
    ):
        """Konto z `en` dostaje angielski temat."""
        user = ProfileFactory(preferred_language=PreferredLanguage.EN).user

        with patch(NOTIFY_MAIL) as send:
            with django_capture_on_commit_callbacks(execute=True):
                notify(user, NotificationKind.ORDER_PAID, {"order_number": "A1"})

        assert send.call_args.kwargs["subject"] == "Order A1 paid"

    def test_account_without_language_gets_polish(
        self, django_capture_on_commit_callbacks
    ):
        """Konto bez wartości dostaje maila po polsku."""
        user = ProfileFactory().user

        with patch(NOTIFY_MAIL) as send:
            with django_capture_on_commit_callbacks(execute=True):
                notify(user, NotificationKind.ORDER_PAID, {"order_number": "A1"})

        assert send.call_args.kwargs["subject"] == "Zamówienie A1 opłacone"

    def test_guest_language_passed_explicitly(self, django_capture_on_commit_callbacks):
        """Gość: język z zamówienia przekazany przez wywołującego."""
        with patch(NOTIFY_MAIL) as send:
            with django_capture_on_commit_callbacks(execute=True):
                notify(
                    "guest@test.com",
                    NotificationKind.ORDER_PAID,
                    {"order_number": "A1"},
                    language="en",
                )

        assert send.call_args.kwargs["subject"] == "Order A1 paid"

    @pytest.mark.parametrize(("language", "prefix"), [("en", "/en/"), (None, "/pl/")])
    def test_cart_reminder_links_carry_language(
        self, django_capture_on_commit_callbacks, language, prefix
    ):
        """Przypomnienie o koszyku: linki z prefiksem języka konta."""
        from apps.notifications.models import NotificationPreference
        from tests.factories.orders import CartFactory

        user = ProfileFactory(preferred_language=language).user
        NotificationPreference.objects.create(user=user, marketing_email=True)
        cart = CartFactory(user=user)
        variant = ProductVariantFactory(product=PublishedProductFactory())
        stock(variant, 5)
        add_item(cart, variant=variant, quantity=1)
        now = cart.updated_at + datetime.timedelta(days=30)

        with patch(NOTIFY_MAIL) as send:
            with django_capture_on_commit_callbacks(execute=True):
                assert send_cart_reminder(cart.pk, now=now)

        body = send.call_args.kwargs["body"]
        assert f"{settings.FRONTEND_URL}{prefix}cart" in body
        assert f"{settings.FRONTEND_URL}{prefix}account/notifications" in body
        assert f"{settings.FRONTEND_URL}{prefix}newsletter/unsubscribe/" in body


@pytest.mark.django_db
class TestLanguageStoredAtCreation:
    """Język zapisywany przy rejestracji, zamówieniu gościa i zapisie na newsletter."""

    def test_guest_order_stores_accept_language(self, api_client: APIClient):
        """Zamówienie gościa z `Accept-Language: en-GB` zapisuje `en`."""
        email = "gosc@test.com"
        GuestConsentFactory(
            email=email,
            document=ConsentDocumentFactory(kind=ConsentKind.TERMS),
        )
        cart = GuestCartFactory()
        variant = ProductVariantFactory(product=PublishedProductFactory(), price=10000)
        stock(variant, 5)
        add_item(cart, variant=variant, quantity=1)
        method = ShippingMethodFactory()

        response: Any = api_client.post(
            reverse("order-list"),
            {
                "recipientName": "Jan Kowalski",
                "street": "Złota 44",
                "city": "Warszawa",
                "postalCode": "00-120",
                "country": "PL",
                "shippingMethod": str(method.pk),
                "email": email,
            },
            HTTP_X_CART_TOKEN=cart.session_key,
            HTTP_ACCEPT_LANGUAGE="en-GB,en;q=0.9",
        )

        assert response.status_code == status.HTTP_201_CREATED
        order = Order.objects.get(number=response.json()["number"])
        assert order.preferred_language == "en"

    @pytest.mark.parametrize(
        ("extra", "header", "expected"),
        [
            ({}, "de", "en"),
            ({}, "pl-PL", "pl"),
            ({"preferred_language": "pl"}, "de", "pl"),
        ],
    )
    def test_signup_stores_language(
        self, api_client: APIClient, consent_documents, extra, header, expected
    ):
        """Pole formularza wygrywa; bez niego decyduje `Accept-Language`."""
        api_client.post(
            "/_allauth/app/v1/auth/signup",
            {
                "email": "lang-signup@test.com",
                "password": "testpass123!",
                "consent_terms": True,
                "consent_privacy": True,
                **extra,
            },
            format="json",
            HTTP_ACCEPT_LANGUAGE=header,
        )

        user = CustomUser.objects.get(email="lang-signup@test.com")
        assert Profile.objects.get(user=user).preferred_language == expected

    def test_newsletter_subscription_stores_language_and_mails_in_it(
        self, api_client: APIClient, django_capture_on_commit_callbacks
    ):
        """Subskrypcja zapisuje język; mail potwierdzenia idzie w nim."""
        ConsentDocumentFactory(kind=ConsentKind.MARKETING)

        with patch(NEWSLETTER_MAIL) as send:
            with django_capture_on_commit_callbacks(execute=True):
                response: Any = api_client.post(
                    reverse("newsletter-subscribe"),
                    {"email": "lang@test.com"},
                    format="json",
                    HTTP_ACCEPT_LANGUAGE="en",
                )

        assert response.status_code < 300
        subscription = NewsletterSubscription.objects.get(email="lang@test.com")
        assert subscription.preferred_language == "en"
        assert (
            send.call_args.kwargs["subject"] == "Confirm your newsletter subscription"
        )
        assert (
            f"{settings.FRONTEND_URL}/en/newsletter/confirm/"
            in (send.call_args.kwargs["body"])
        )


def test_every_notification_kind_has_english_template():
    """Każdy rodzaj z `_TEMPLATES` ma wersję angielską."""
    from apps.notifications.services import _TEMPLATES, _TEMPLATES_EN

    assert set(_TEMPLATES_EN) == set(_TEMPLATES)


@pytest.mark.django_db
class TestReviewFixes:
    """Ogłoszenie promocji, kod anonimizacji i ponowny zapis w języku odbiorcy."""

    def test_promotion_announcement_in_recipient_language(self):
        """Konto `en` i subskrypcja `en` dostają angielski temat i link `/en/`."""
        from typing import cast

        from apps.notifications.models import NewsletterStatus, NotificationPreference
        from apps.notifications.tasks import announce_promotion
        from tests.factories.promotions import PromotionFactory

        account = ProfileFactory(
            preferred_language="en", user__email="acc@test.com"
        ).user
        NotificationPreference.objects.create(user=account, marketing_email=True)
        NewsletterSubscription.objects.create(
            email="en@test.com",
            status=NewsletterStatus.ACTIVE,
            preferred_language="en",
        )
        NewsletterSubscription.objects.create(
            email="pl@test.com", status=NewsletterStatus.ACTIVE
        )
        promotion = PromotionFactory(name="Autumn")

        with (
            patch(NEWSLETTER_MAIL) as send,
            patch("apps.notifications.tasks.send_push_notification"),
        ):
            cast(Any, announce_promotion)(promotion_id=str(promotion.pk))

        mails = {call.kwargs["to"]: call.kwargs for call in send.call_args_list}
        for address in ("acc@test.com", "en@test.com"):
            assert mails[address]["subject"] == "New promotion: Autumn"
            assert (
                f"{settings.FRONTEND_URL}/en/newsletter/unsubscribe/"
                in (mails[address]["body"])
            )
            assert "List-Unsubscribe" in mails[address]["headers"]
        assert mails["pl@test.com"]["subject"] == "Nowa promocja: Autumn"
        assert f"{settings.FRONTEND_URL}/pl/" in mails["pl@test.com"]["body"]

    def test_anonymisation_code_in_account_language(
        self, django_capture_on_commit_callbacks
    ):
        """Kod usunięcia konta idzie po angielsku do konta `en`."""
        from apps.accounts.services.anonymisation_code import send_code

        user = ProfileFactory(preferred_language="en").user

        with patch(
            "apps.accounts.services.anonymisation_code.send_notification_email"
        ) as send:
            with django_capture_on_commit_callbacks(execute=True):
                send_code(user)

        assert send.call_args.kwargs["subject"] == "Account deletion confirmation code"

    def test_resubscribe_without_header_keeps_language(self):
        """Ponowny zapis bez nagłówka nie kasuje języka; nowy język go odświeża."""
        from apps.notifications import newsletter
        from apps.notifications.models import NewsletterStatus

        ConsentDocumentFactory(kind=ConsentKind.MARKETING)
        NewsletterSubscription.objects.create(
            email="keep@test.com",
            status=NewsletterStatus.UNSUBSCRIBED,
            preferred_language="en",
        )
        NewsletterSubscription.objects.create(email="pending@test.com")

        with patch(NEWSLETTER_MAIL):
            newsletter.subscribe("keep@test.com", language=None)
            newsletter.subscribe("pending@test.com", language="en")

        assert (
            NewsletterSubscription.objects.get(email="keep@test.com").preferred_language
            == "en"
        )
        assert (
            NewsletterSubscription.objects.get(
                email="pending@test.com"
            ).preferred_language
            == "en"
        )
