"""Reset hasła kodem z maila, bez linku z kluczem (#313, ADR 0038)."""

from __future__ import annotations

import json
import re
from typing import cast

import pytest
from django.core import mail
from rest_framework.response import Response
from rest_framework.test import APIClient

from tests.factories.accounts import UserFactory

REQUEST_URL = "/_allauth/app/v1/auth/password/request"
RESET_URL = "/_allauth/app/v1/auth/password/reset"

pytestmark = pytest.mark.django_db


def _session_token(response: Response) -> str:
    return json.loads(response.content)["meta"]["session_token"]


class TestPasswordResetByCode:
    """Żądanie resetu wysyła kod, a kod z nowym hasłem ustawia hasło."""

    def test_request_sends_code_not_link(
        self, api_client: APIClient, django_capture_on_commit_callbacks
    ):
        """Mail resetu niesie kod i nie zawiera żadnego linku."""
        UserFactory(email="reset@test.com")

        with django_capture_on_commit_callbacks(execute=True):
            response = cast(
                Response,
                api_client.post(
                    REQUEST_URL, {"email": "reset@test.com"}, format="json"
                ),
            )

        assert response.status_code == 401
        flows = json.loads(response.content)["data"]["flows"]
        assert any(
            f["id"] == "password_reset_by_code" and f.get("is_pending") for f in flows
        )
        assert len(mail.outbox) == 1
        assert "http" not in mail.outbox[0].body

    def test_code_and_password_reset_password(
        self, api_client: APIClient, django_capture_on_commit_callbacks
    ):
        """Kod z maila + nowe hasło w jednym żądaniu zmieniają hasło (jak mobile)."""
        user = UserFactory(email="code@test.com")

        with django_capture_on_commit_callbacks(execute=True):
            response = cast(
                Response,
                api_client.post(REQUEST_URL, {"email": "code@test.com"}, format="json"),
            )
        code = re.search(r"^\s*([A-Z0-9-]{4,})\s*$", str(mail.outbox[0].body), re.M)
        assert code is not None

        api_client.credentials(HTTP_X_SESSION_TOKEN=_session_token(response))
        reset = cast(
            Response,
            api_client.post(
                RESET_URL,
                {"key": code.group(1), "password": "N0we-haslo-313!"},
                format="json",
            ),
        )

        assert reset.status_code == 401
        user.refresh_from_db()
        assert user.check_password("N0we-haslo-313!")


class TestPasswordResetRateLimits:
    """Natywne statusy przy przekroczeniu limitów resetu hasła (#421)."""

    def test_request_limit_returns_429_without_error_code(
        self, api_client: APIClient, django_capture_on_commit_callbacks
    ):
        """Szóste zamówienie resetu na ten sam adres dostaje 429 bez kodu błędu.

        Allauth pilnuje `reset_password` przez `consume_or_429`, więc limit
        zamówienia resetu to `RateLimitResponse`, a nie walidacja z kodem jak
        przy logowaniu kodem (#414, ADR 0040).
        """
        UserFactory(email="reset-limit@test.com")

        for _ in range(5):
            response = cast(
                Response,
                api_client.post(
                    REQUEST_URL, {"email": "reset-limit@test.com"}, format="json"
                ),
            )
            assert response.status_code == 401

        with django_capture_on_commit_callbacks(execute=True):
            limited = cast(
                Response,
                api_client.post(
                    REQUEST_URL, {"email": "reset-limit@test.com"}, format="json"
                ),
            )

        assert limited.status_code == 429
        assert json.loads(limited.content) == {"status": 429}

    def test_reset_code_attempt_limit_ends_the_stage(
        self, api_client: APIClient, django_capture_on_commit_callbacks, settings
    ):
        """Błędny kod zużywa próby; próba po limicie trafia na 409 bez etapu.

        Allauth liczy nieudane potwierdzenia kodu resetu i po
        `PASSWORD_RESET_BY_CODE_MAX_ATTEMPTS` kasuje etap z sesji, więc kolejne
        ustawienie hasła dostaje `ConflictResponse` — tak samo jak przy
        logowaniu kodem, tylko bez wcześniejszego 400 z kodem limitu.
        """
        settings.ACCOUNT_PASSWORD_RESET_BY_CODE_MAX_ATTEMPTS = 3
        UserFactory(email="reset-attempts@test.com")

        with django_capture_on_commit_callbacks(execute=True):
            response = cast(
                Response,
                api_client.post(
                    REQUEST_URL, {"email": "reset-attempts@test.com"}, format="json"
                ),
            )
        api_client.credentials(HTTP_X_SESSION_TOKEN=_session_token(response))

        statuses = []
        bodies = []
        for _ in range(4):
            reset = cast(
                Response,
                api_client.post(
                    RESET_URL,
                    {"key": "AAAA-AAAA", "password": "N0we-haslo-421!"},
                    format="json",
                ),
            )
            statuses.append(reset.status_code)
            bodies.append(json.loads(reset.content))

        assert statuses == [400, 400, 400, 409]
        rejected = bodies[0]["errors"][0]
        assert (rejected["param"], rejected["code"]) == ("key", "incorrect_code")
        assert bodies[-1] == {"status": 409}
