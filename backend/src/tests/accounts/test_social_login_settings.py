from __future__ import annotations

from urllib.parse import parse_qs, urlparse

from allauth.socialaccount import app_settings as socialaccount_settings
from allauth.socialaccount.models import SocialApp
from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from django.conf import settings
from django.test import RequestFactory, override_settings


def test_social_login_does_not_authenticate_existing_user_by_email():
    """Login społecznościowy nie wpina się w istniejące konto po samym e-mailu."""
    assert socialaccount_settings.EMAIL_AUTHENTICATION is False
    assert settings.SOCIALACCOUNT_PROVIDERS["google"]["EMAIL_AUTHENTICATION"] is False


def test_allauth_builds_google_redirect_uri_from_forwarded_headers(rf: RequestFactory):
    """Allauth buduje redirect_uri callbacku Google na publicznym hoście z nagłówków proxy."""
    request = rf.get(
        "/_allauth/browser/v1/auth/provider/redirect",
        HTTP_HOST="internal-backend:8000",
        HTTP_X_FORWARDED_HOST="olivin.pl",
        HTTP_X_FORWARDED_PROTO="https",
    )

    with override_settings(
        ALLOWED_HOSTS=["internal-backend", "olivin.pl"],
        USE_X_FORWARDED_HOST=True,
        SECURE_PROXY_SSL_HEADER=("HTTP_X_FORWARDED_PROTO", "https"),
    ):
        adapter = GoogleOAuth2Adapter(request)
        callback_url = adapter.get_callback_url(request, None)
        assert callback_url == "https://olivin.pl/accounts/google/login/callback/"

        app = SocialApp(provider="google", client_id="google-client-id")
        client = adapter.get_client(request, app)
        auth_url = client.get_redirect_url(
            adapter.authorize_url, ["email", "profile"], {}
        )
        query_params = parse_qs(urlparse(auth_url).query)
        assert query_params["redirect_uri"] == [
            "https://olivin.pl/accounts/google/login/callback/"
        ]


def test_allauth_builds_facebook_redirect_uri_from_forwarded_headers(
    rf: RequestFactory,
):
    """Allauth buduje redirect_uri callbacku Facebook na publicznym hoście z nagłówków proxy."""
    request = rf.get(
        "/_allauth/browser/v1/auth/provider/redirect",
        HTTP_HOST="internal-backend:8000",
        HTTP_X_FORWARDED_HOST="olivin.pl",
        HTTP_X_FORWARDED_PROTO="https",
    )

    with override_settings(
        ALLOWED_HOSTS=["internal-backend", "olivin.pl"],
        USE_X_FORWARDED_HOST=True,
        SECURE_PROXY_SSL_HEADER=("HTTP_X_FORWARDED_PROTO", "https"),
    ):
        adapter = FacebookOAuth2Adapter(request)
        callback_url = adapter.get_callback_url(request, None)
        assert callback_url == "https://olivin.pl/accounts/facebook/login/callback/"

        app = SocialApp(provider="facebook", client_id="fb-client-id")
        client = adapter.get_client(request, app)
        auth_url = client.get_redirect_url(
            adapter.authorize_url, ["email", "public_profile"], {}
        )
        query_params = parse_qs(urlparse(auth_url).query)
        assert query_params["redirect_uri"] == [
            "https://olivin.pl/accounts/facebook/login/callback/"
        ]


def test_allauth_callback_url_ignores_forwarded_headers_without_proxy_settings(
    rf: RequestFactory,
):
    """Bez USE_X_FORWARDED_HOST i SECURE_PROXY_SSL_HEADER allauth ignoruje nagłówki proxy."""
    request = rf.get(
        "/_allauth/browser/v1/auth/provider/redirect",
        HTTP_HOST="internal-backend:8000",
        HTTP_X_FORWARDED_HOST="olivin.pl",
        HTTP_X_FORWARDED_PROTO="https",
    )

    with override_settings(
        ALLOWED_HOSTS=["internal-backend"],
        USE_X_FORWARDED_HOST=False,
        SECURE_PROXY_SSL_HEADER=None,
    ):
        adapter = GoogleOAuth2Adapter(request)
        callback_url = adapter.get_callback_url(request, None)
        assert (
            callback_url
            == "http://internal-backend:8000/accounts/google/login/callback/"
        )
