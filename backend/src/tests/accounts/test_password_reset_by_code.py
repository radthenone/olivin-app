"""Reset hasła kodem z maila, bez linku z kluczem (#313, ADR 0038)."""

from __future__ import annotations

import json
import re

import pytest
from django.core import mail
from django.http import HttpResponse
from rest_framework.test import APIClient

from tests.factories.accounts import UserFactory

REQUEST_URL = "/_allauth/app/v1/auth/password/request"
RESET_URL = "/_allauth/app/v1/auth/password/reset"

pytestmark = pytest.mark.django_db


def _session_token(response: HttpResponse) -> str:
    return json.loads(response.content)["meta"]["session_token"]


class TestPasswordResetByCode:
    """Żądanie resetu wysyła kod, a kod z nowym hasłem ustawia hasło."""

    def test_request_sends_code_not_link(
        self, api_client: APIClient, django_capture_on_commit_callbacks
    ):
        """Mail resetu niesie kod i nie zawiera żadnego linku."""
        UserFactory(email="reset@test.com")

        with django_capture_on_commit_callbacks(execute=True):
            response = api_client.post(
                REQUEST_URL, {"email": "reset@test.com"}, format="json"
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
            response = api_client.post(
                REQUEST_URL, {"email": "code@test.com"}, format="json"
            )
        code = re.search(r"^\s*([A-Z0-9-]{4,})\s*$", mail.outbox[0].body, re.M)
        assert code is not None

        api_client.credentials(HTTP_X_SESSION_TOKEN=_session_token(response))
        reset = api_client.post(
            RESET_URL,
            {"key": code.group(1), "password": "N0we-haslo-313!"},
            format="json",
        )

        assert reset.status_code == 401
        user.refresh_from_db()
        assert user.check_password("N0we-haslo-313!")
