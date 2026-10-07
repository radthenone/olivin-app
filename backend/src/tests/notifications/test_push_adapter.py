"""Adapter Expo: odpowiedź, martwe tokeny, awaria sieci (#202)."""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest
import requests

from core.integrations.push.base import PushProviderError
from core.integrations.push.expo import ExpoPushProvider
from core.integrations.push.noop import NoopPushProvider


def _response(payload: dict) -> Mock:
    response = Mock()
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    return response


class TestExpoPushProvider:
    """Adapter push Expo."""

    def test_returns_invalid_tokens(self):
        """Adapter zwraca nieważne tokeny."""
        provider = ExpoPushProvider()
        payload = {
            "data": [
                {"status": "ok"},
                {
                    "status": "error",
                    "message": "Device is not registered",
                    "details": {"error": "DeviceNotRegistered"},
                },
            ]
        }

        with patch("requests.post", return_value=_response(payload)) as post:
            invalid = provider.send_push(
                tokens=["ExponentPushToken[a]", "ExponentPushToken[b]"],
                title="Tytuł",
                body="Treść",
                data={},
            )

        assert invalid == ["ExponentPushToken[b]"]
        sent_json = post.call_args.kwargs["json"]
        assert [message["to"] for message in sent_json] == [
            "ExponentPushToken[a]",
            "ExponentPushToken[b]",
        ]

    def test_other_errors_not_treated_as_invalid(self):
        """Inne błędy nie unieważniają tokenu."""
        provider = ExpoPushProvider()
        payload = {
            "data": [
                {
                    "status": "error",
                    "message": "Message too big",
                    "details": {"error": "MessageTooBig"},
                }
            ]
        }

        with patch("requests.post", return_value=_response(payload)):
            assert (
                provider.send_push(
                    tokens=["ExponentPushToken[a]"],
                    title="T",
                    body="B",
                    data={},
                )
                == []
            )

    def test_network_error_raises_provider_error(self):
        """Błąd sieci kończy się błędem operatora."""
        provider = ExpoPushProvider()

        with patch("requests.post", side_effect=requests.ConnectionError("padło")):
            with pytest.raises(PushProviderError):
                provider.send_push(
                    tokens=["ExponentPushToken[a]"],
                    title="T",
                    body="B",
                    data={},
                )

    def test_empty_tokens_no_request(self):
        """Bez tokenów nie ma żądania."""
        provider = ExpoPushProvider()

        with patch("requests.post") as post:
            assert provider.send_push(tokens=[], title="T", body="B", data={}) == []

        post.assert_not_called()


class TestNoopPushProvider:
    """Adapter push, który niczego nie wysyła."""

    def test_sends_nothing(self):
        """Adapter niczego nie wysyła."""
        assert (
            NoopPushProvider().send_push(
                tokens=["ExponentPushToken[a]"], title="T", body="B", data={}
            )
            == []
        )
