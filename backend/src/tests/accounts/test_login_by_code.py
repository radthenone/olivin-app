"""Logowanie kodem z maila przez headless API allauth (#407, ADR 0038)."""

from __future__ import annotations

import re
from typing import cast

import pytest
from allauth.account.models import EmailAddress
from allauth.mfa.models import Authenticator
from django.core import mail
from freezegun import freeze_time
from rest_framework.response import Response
from rest_framework.test import APIClient

from tests.factories.accounts import UserFactory

CLIENTS = ("app", "browser")

pytestmark = pytest.mark.django_db


def _urls(client: str) -> tuple[str, str, str]:
    """Adresy zamówienia, potwierdzenia kodu i sesji dla klienta headless."""
    return (
        f"/_allauth/{client}/v1/auth/code/request",
        f"/_allauth/{client}/v1/auth/code/confirm",
        f"/_allauth/{client}/v1/auth/session",
    )


def _code_from_last_mail() -> str:
    """Kod logowania z ostatniej wiadomości, tak jak przepisuje go człowiek."""
    body = str(mail.outbox[-1].body)
    code = re.search(r"^\s*([A-Z0-9-]{4,})\s*$", body, re.M)
    assert code is not None, body
    return code.group(1)


def _user(email: str):
    """Użytkownik z zweryfikowanym adresem e-mail, gotowy do logowania kodem."""
    user = UserFactory(email=email)
    EmailAddress.objects.create(user=user, email=email, verified=True, primary=True)
    return user


def _request_code(
    api_client: APIClient,
    client: str,
    email: str,
    capture_on_commit,
    parse,
) -> Response:
    """Zamawia kod i przygotowuje klienta do potwierdzenia."""
    request_url, _, _ = _urls(client)
    with capture_on_commit(execute=True):
        response = cast(
            Response, api_client.post(request_url, {"email": email}, format="json")
        )
    meta = parse(response).get("meta", {})
    if client == "app" and "session_token" in meta:
        api_client.credentials(HTTP_X_SESSION_TOKEN=meta["session_token"])
    return response


def _confirm_code(api_client: APIClient, client: str, code: str) -> Response:
    """Potwierdza kod w ramach sesji założonej przy zamówieniu."""
    _, confirm_url, _ = _urls(client)
    return cast(Response, api_client.post(confirm_url, {"code": code}, format="json"))


class TestLoginByCode:
    """Poprawny kod loguje, a kod po terminie jest odrzucany."""

    @pytest.mark.parametrize("client", CLIENTS)
    def test_valid_code_logs_user_in(
        self,
        client,
        api_client: APIClient,
        django_capture_on_commit_callbacks,
        request_response,
    ):
        """Kod z maila potwierdzony w tej samej sesji zakłada zalogowaną sesję."""
        _user("login-code@test.com")

        request = _request_code(
            api_client,
            client,
            "login-code@test.com",
            django_capture_on_commit_callbacks,
            request_response,
        )
        assert request.status_code == 401

        confirm = _confirm_code(api_client, client, _code_from_last_mail())

        assert confirm.status_code == 200, confirm.content
        assert request_response(confirm)["data"]["user"]["email"] == (
            "login-code@test.com"
        )
        assert request_response(confirm)["meta"]["is_authenticated"] is True
        if client == "app":
            api_client.credentials(
                HTTP_X_SESSION_TOKEN=request_response(confirm)["meta"]["session_token"]
            )

        _, _, session_url = _urls(client)
        session = cast(Response, api_client.get(session_url))

        assert session.status_code == 200
        assert request_response(session)["data"]["user"]["email"] == (
            "login-code@test.com"
        )

    @pytest.mark.parametrize("client", CLIENTS)
    def test_expired_code_is_rejected(
        self,
        client,
        api_client: APIClient,
        django_capture_on_commit_callbacks,
        request_response,
    ):
        """Kod potwierdzony po 180 sekundach nie zakłada sesji."""
        _user("expired@test.com")

        with freeze_time("2026-01-01 12:00:00"):
            _request_code(
                api_client,
                client,
                "expired@test.com",
                django_capture_on_commit_callbacks,
                request_response,
            )
            code = _code_from_last_mail()

        with freeze_time("2026-01-01 12:03:01"):
            confirm = _confirm_code(api_client, client, code)

        assert confirm.status_code == 409
        meta = request_response(confirm).get("meta", {})
        assert meta.get("is_authenticated", False) is False
        assert "session_token" not in meta


class TestEnumerationPrevention:
    """Nieznany e-mail nie zdradza, że konto nie istnieje."""

    @pytest.mark.parametrize("client", CLIENTS)
    def test_unknown_email_gets_same_response_as_known(
        self,
        client,
        api_client: APIClient,
        django_capture_on_commit_callbacks,
        request_response,
    ):
        """Odpowiedź dla nieznanego adresu jest taka sama jak dla znanego."""
        _user("known@test.com")

        known = _request_code(
            api_client,
            client,
            "known@test.com",
            django_capture_on_commit_callbacks,
            request_response,
        )
        unknown = _request_code(
            APIClient(),
            client,
            "ghost@test.com",
            django_capture_on_commit_callbacks,
            request_response,
        )

        assert known.status_code == unknown.status_code == 401
        known_body, unknown_body = request_response(known), request_response(unknown)
        assert known_body["data"] == unknown_body["data"]

        def without_session_token(body: dict) -> dict:
            return {k: v for k, v in body["meta"].items() if k != "session_token"}

        assert without_session_token(known_body) == without_session_token(unknown_body)
        assert known_body["meta"]["is_authenticated"] is False
        assert unknown_body["meta"]["is_authenticated"] is False
        assert len(mail.outbox) == 2


class TestMfaAfterLoginByCode:
    """Konto z MFA po kodzie czeka na drugi składnik, nie dostaje sesji."""

    @pytest.mark.parametrize("client", CLIENTS)
    def test_mfa_account_gets_pending_stage_not_session(
        self,
        client,
        api_client: APIClient,
        django_capture_on_commit_callbacks,
        request_response,
    ):
        """Poprawny kod zatrzymuje logowanie na etapie `mfa_authenticate`."""
        user = _user("mfa@test.com")
        Authenticator.objects.create(
            user=user,
            type=Authenticator.Type.TOTP,
            data={"secret": "JBSWY3DPEHPK3PXP"},
        )

        _request_code(
            api_client,
            client,
            "mfa@test.com",
            django_capture_on_commit_callbacks,
            request_response,
        )
        confirm = _confirm_code(api_client, client, _code_from_last_mail())

        assert confirm.status_code == 401
        body = request_response(confirm)
        flows = {flow["id"]: flow for flow in body["data"]["flows"]}
        assert flows["mfa_authenticate"]["is_pending"] is True
        assert body["meta"]["is_authenticated"] is False
        assert "session_token" not in body["meta"]


class TestLoginByCodeRateLimits:
    """Natywne statusy przy przekroczeniu limitów logowania kodem."""

    @pytest.mark.parametrize("client", CLIENTS)
    def test_request_limit_returns_400(
        self,
        client,
        api_client: APIClient,
        django_capture_on_commit_callbacks,
        request_response,
    ):
        """Czwarte zamówienie kodu na ten sam adres w minucie jest odrzucane błędem walidacji."""
        _user("request-limit@test.com")

        for _ in range(3):
            response = _request_code(
                api_client,
                client,
                "request-limit@test.com",
                django_capture_on_commit_callbacks,
                request_response,
            )
            assert response.status_code == 401

        limited = _request_code(
            api_client,
            client,
            "request-limit@test.com",
            django_capture_on_commit_callbacks,
            request_response,
        )

        assert limited.status_code == 400

    @pytest.mark.parametrize("client", CLIENTS)
    def test_ip_limit_applies_without_per_key_limit(
        self,
        client,
        api_client: APIClient,
        django_capture_on_commit_callbacks,
        request_response,
    ):
        """Dwudziesty pierwszy zamówienia z jednego IP są odrzucane, choć każdy adres ma własny klucz."""
        for i in range(20):
            response = _request_code(
                api_client,
                client,
                f"ip-limit-{i}@test.com",
                django_capture_on_commit_callbacks,
                request_response,
            )
            assert response.status_code == 401

        limited = _request_code(
            api_client,
            client,
            "ip-limit-20@test.com",
            django_capture_on_commit_callbacks,
            request_response,
        )

        assert limited.status_code == 400

    @pytest.mark.parametrize("client", CLIENTS)
    def test_confirm_limit_returns_400_then_409(
        self,
        client,
        api_client: APIClient,
        django_capture_on_commit_callbacks,
        request_response,
        settings,
    ):
        """Błędne kody zużywają limit; próba, która go dobija, daje 400, kolejne 409."""
        settings.ACCOUNT_LOGIN_BY_CODE_MAX_ATTEMPTS = 3
        _user("confirm-limit@test.com")

        _request_code(
            api_client,
            client,
            "confirm-limit@test.com",
            django_capture_on_commit_callbacks,
            request_response,
        )
        statuses = [
            _confirm_code(api_client, client, "AAAA-AAAA").status_code for _ in range(4)
        ]

        assert statuses == [400, 400, 400, 409]
