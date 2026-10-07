from __future__ import annotations

import json
from typing import cast

import pytest
from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount, SocialLogin
from django.test import RequestFactory
from rest_framework.response import Response
from rest_framework.test import APIClient

from apps.accounts.models import CustomUser, Profile
from apps.consents.models import Consent, ConsentKind
from apps.notifications.models import NotificationPreference
from core.services.allauth.social_adapter import SocialAccountAdapter
from tests.factories.consents import ConsentDocumentFactory

SIGNUP_URL = "/_allauth/app/v1/auth/signup"
REQUIRED_CONSENTS = {"consent_terms": True, "consent_privacy": True}

pytestmark = pytest.mark.django_db


def _signup(client: APIClient, email: str, **consents: bool) -> Response:
    return cast(
        Response,
        client.post(
            SIGNUP_URL,
            {"email": email, "password": "testpass123!", **consents},
            format="json",
        ),
    )


def _errors(response: Response) -> list[dict]:
    return json.loads(response.content)["errors"]


class TestEmailSignupConsents:
    """Rejestracja e-mailem wymaga zgód na regulamin i politykę prywatności."""

    def test_signup_with_required_consents_records_current_versions(
        self, api_client: APIClient, consent_documents
    ):
        """Komplet wymaganych zgód → konto, profil i Consent z bieżącą wersją."""
        _signup(api_client, "full@test.com", **REQUIRED_CONSENTS)

        user = CustomUser.objects.get(email="full@test.com")
        assert Profile.objects.filter(user=user).exists()
        consents = {c.kind: c.version for c in Consent.objects.filter(user=user)}
        assert consents == {"terms": "terms-2026", "privacy": "privacy-2026"}
        assert not NotificationPreference.for_user(user).marketing_email

    def test_signup_without_terms_is_rejected(
        self, api_client: APIClient, consent_documents
    ):
        """Bez zgody na regulamin → 400, konto nie powstaje."""
        response = _signup(api_client, "noterms@test.com", consent_privacy=True)

        assert response.status_code == 400
        assert any(e.get("param") == "consent_terms" for e in _errors(response))
        assert not CustomUser.objects.filter(email="noterms@test.com").exists()
        assert not Consent.objects.exists()

    def test_signup_with_marketing_sets_preference(
        self, api_client: APIClient, consent_documents
    ):
        """Zgoda marketingowa → Consent marketing i marketing_email=True."""
        _signup(api_client, "mkt@test.com", consent_marketing=True, **REQUIRED_CONSENTS)

        user = CustomUser.objects.get(email="mkt@test.com")
        kinds = set(
            Consent.objects.filter(user=user).values_list("document__kind", flat=True)
        )
        assert kinds == {"terms", "privacy", "marketing"}
        assert NotificationPreference.for_user(user).marketing_email

    def test_missing_current_document_rejects_signup(self, api_client: APIClient):
        """Brak bieżącej wersji regulaminu → czytelny błąd, konto nie powstaje."""
        ConsentDocumentFactory(kind=ConsentKind.PRIVACY)

        response = _signup(api_client, "nodoc@test.com", **REQUIRED_CONSENTS)

        assert response.status_code == 400
        assert any("konfiguracji" in e["message"] for e in _errors(response))
        assert not CustomUser.objects.filter(email="nodoc@test.com").exists()

    def test_missing_marketing_document_ignored_without_marketing_consent(
        self, api_client: APIClient
    ):
        """Brak dokumentu marketingowego nie blokuje rejestracji bez marketingu."""
        ConsentDocumentFactory(kind=ConsentKind.TERMS)
        ConsentDocumentFactory(kind=ConsentKind.PRIVACY)

        _signup(api_client, "nomkt@test.com", **REQUIRED_CONSENTS)

        assert CustomUser.objects.filter(email="nomkt@test.com").exists()

    def test_marketing_consent_without_marketing_document_is_rejected(
        self, api_client: APIClient
    ):
        """Zaznaczony marketing bez bieżącego dokumentu → błąd konfiguracji."""
        ConsentDocumentFactory(kind=ConsentKind.TERMS)
        ConsentDocumentFactory(kind=ConsentKind.PRIVACY)

        response = _signup(
            api_client, "badmkt@test.com", consent_marketing=True, **REQUIRED_CONSENTS
        )

        assert response.status_code == 400
        assert not CustomUser.objects.filter(email="badmkt@test.com").exists()


PROVIDER_SIGNUP_URL = "/_allauth/browser/v1/auth/provider/signup"


def _pending_social_signup(client: APIClient, email: str) -> None:
    """Stan po powrocie od Google bez konta: logowanie czeka na dokończenie."""
    provider = SocialAccountAdapter().get_provider(RequestFactory().get("/"), "google")
    sociallogin = SocialLogin(
        provider=provider,
        user=CustomUser(email=email),
        account=SocialAccount(
            provider="google", uid=f"uid-{email}", extra_data={"email": email}
        ),
        email_addresses=[EmailAddress(email=email, verified=True, primary=True)],
    )
    session = client.session
    session["socialaccount_sociallogin"] = sociallogin.serialize()
    session.save()


class TestProviderSignupConsents:
    """Dokończenie rejestracji po logowaniu zewnętrznym wymaga tych samych zgód."""

    def test_auto_signup_disabled(self, rf):
        """Konto z Google nie powstaje samo — klient przechodzi krok provider signup."""
        sociallogin = SocialLogin(
            user=CustomUser(email="auto@test.com"),
            account=SocialAccount(provider="google", uid="auto"),
        )
        assert not SocialAccountAdapter().is_auto_signup_allowed(
            rf.get("/"), sociallogin
        )

    def test_provider_signup_without_consents_is_rejected(
        self, api_client: APIClient, consent_documents
    ):
        """Brak zgód w provider signup → 400, konto nie powstaje."""
        _pending_social_signup(api_client, "g-none@test.com")

        response = cast(
            Response,
            api_client.post(
                PROVIDER_SIGNUP_URL, {"email": "g-none@test.com"}, format="json"
            ),
        )

        assert response.status_code == 400
        assert not CustomUser.objects.filter(email="g-none@test.com").exists()

    def test_provider_signup_with_consents_creates_account(
        self, api_client: APIClient, consent_documents
    ):
        """Komplet zgód → konto, konto społecznościowe i zgody w jednej operacji."""
        _pending_social_signup(api_client, "g-ok@test.com")

        api_client.post(
            PROVIDER_SIGNUP_URL,
            {"email": "g-ok@test.com", "consent_marketing": True, **REQUIRED_CONSENTS},
            format="json",
        )

        user = CustomUser.objects.get(email="g-ok@test.com")
        assert SocialAccount.objects.filter(user=user, provider="google").exists()
        kinds = set(
            Consent.objects.filter(user=user).values_list("document__kind", flat=True)
        )
        assert kinds == {"terms", "privacy", "marketing"}
        assert NotificationPreference.for_user(user).marketing_email

    def test_existing_social_account_logs_in_without_signup(self, user: CustomUser):
        """Istniejące konto społecznościowe jest rozpoznane — bez kroku signup."""
        SocialAccount.objects.create(user=user, provider="google", uid="known")
        sociallogin = SocialLogin(
            user=CustomUser(email=user.email),
            account=SocialAccount(provider="google", uid="known"),
        )

        sociallogin.lookup()

        assert sociallogin.is_existing
        assert sociallogin.user == user
