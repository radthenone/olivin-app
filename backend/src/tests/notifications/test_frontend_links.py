"""Linki z maili składane z jednej bazy `FRONTEND_URL` (#313, ADR 0038)."""

from __future__ import annotations

import pytest
from allauth.core.exceptions import ImmediateHttpResponse
from allauth.headless.socialaccount.internal import on_authentication_error
from django.conf import settings
from django.test import RequestFactory

from apps.notifications import newsletter
from apps.notifications.models import NewsletterSubscription


class TestFrontendLinks:
    """Każdy link z maila zaczyna się od `FRONTEND_URL` z prefiksem języka."""

    @pytest.mark.django_db
    def test_newsletter_links_start_with_frontend_url(self):
        """Potwierdzenie zapisu i wypis prowadzą na `FRONTEND_URL`."""
        subscription = NewsletterSubscription.objects.create(email="n@test.com")
        prefix = f"{settings.FRONTEND_URL}/pl/"

        assert newsletter.confirm_url(subscription).startswith(prefix)
        assert newsletter.subscription_unsubscribe_url(subscription).startswith(prefix)
        assert newsletter.account_unsubscribe_url(1).startswith(prefix)

    def test_all_email_links_derive_from_frontend_url(self):
        """Linki allauth, koszyka i preferencji też wychodzą z `FRONTEND_URL`."""
        prefix = f"{settings.FRONTEND_URL}/pl/"
        urls = [
            *settings.HEADLESS_FRONTEND_URLS.values(),
            settings.CART_URL,
            settings.NOTIFICATION_PREFERENCES_URL,
        ]

        assert all(url.startswith(prefix) for url in urls)

    def test_dead_headless_keys_removed(self):
        """Przy weryfikacji i resecie kodem linki z kluczem są martwe."""
        assert set(settings.HEADLESS_FRONTEND_URLS) == {
            "account_reset_password",
            "account_signup",
            "socialaccount_login_error",
        }

    def test_provider_error_redirects_to_frontend_callback_with_error_code(self):
        """Błąd po stronie providera wraca na callback webu z kodem błędu."""
        request = RequestFactory().get("/")
        state = {"headless": True, "next": None, "process": "login"}

        with pytest.raises(ImmediateHttpResponse) as excinfo:
            on_authentication_error(
                request,
                provider=None,
                error="access_denied",
                extra_context={"state": state},
            )

        assert excinfo.value.response["Location"] == (
            f"{settings.FRONTEND_URL}/pl/auth/provider/callback"
            "?error=access_denied&error_process=login"
        )
