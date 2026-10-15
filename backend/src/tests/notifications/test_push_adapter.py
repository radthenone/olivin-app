"""Adapter Expo: odpowiedź, martwe tokeny, awaria sieci, receipty, retry (#202, #315)."""

from __future__ import annotations

from typing import Any
from unittest.mock import Mock, patch

import pytest
import requests

from apps.notifications.models import PushDevice
from apps.notifications.tasks import check_push_receipts, send_push_notification
from core.integrations.push.base import (
    MARKETING_CHANNEL,
    ORDERS_CHANNEL,
    PushProviderError,
    PushProviderTransientError,
)
from core.integrations.push.expo import ExpoPushProvider
from core.integrations.push.noop import NoopPushProvider
from tests.factories.accounts import UserFactory

EXPO = "core.integrations.push.expo.ExpoPushProvider"


def _response(payload: dict, status_code: int = 200) -> Mock:
    response = Mock()
    response.status_code = status_code
    response.json.return_value = payload
    if status_code >= 400:
        response.raise_for_status.side_effect = requests.HTTPError(
            f"{status_code}", response=response
        )
    else:
        response.raise_for_status.return_value = None
    return response


def _send(provider: ExpoPushProvider, channel: str = ORDERS_CHANNEL) -> Any:
    return provider.send_push(
        tokens=["ExponentPushToken[a]"],
        title="T",
        body="B",
        data={"url": "/orders/X"},
        channel=channel,
    )


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
            result = provider.send_push(
                tokens=["ExponentPushToken[a]", "ExponentPushToken[b]"],
                title="Tytuł",
                body="Treść",
                data={},
                channel=ORDERS_CHANNEL,
            )

        assert result.invalid_tokens == ["ExponentPushToken[b]"]
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
            assert _send(provider).invalid_tokens == []

    def test_network_error_raises_provider_error(self):
        """Błąd sieci kończy się błędem operatora."""
        provider = ExpoPushProvider()

        with patch("requests.post", side_effect=requests.ConnectionError("padło")):
            with pytest.raises(PushProviderTransientError):
                _send(provider)

    def test_empty_tokens_no_request(self):
        """Bez tokenów nie ma żądania."""
        provider = ExpoPushProvider()

        with patch("requests.post") as post:
            result = provider.send_push(
                tokens=[], title="T", body="B", data={}, channel=ORDERS_CHANNEL
            )

        assert result.invalid_tokens == []
        assert result.tickets == {}
        post.assert_not_called()

    def test_transactional_message_has_orders_channel_and_url(self):
        """Wiadomość transakcyjna ma kanał `orders`, wysoki priorytet, dźwięk i `data.url`."""
        payload = {"data": [{"status": "ok", "id": "ticket-a"}]}

        with patch("requests.post", return_value=_response(payload)) as post:
            _send(ExpoPushProvider(), ORDERS_CHANNEL)

        message = post.call_args.kwargs["json"][0]
        assert message["channelId"] == "orders"
        assert message["priority"] == "high"
        assert message["sound"] == "default"
        assert message["data"] == {"url": "/orders/X"}

    def test_marketing_message_has_default_priority(self):
        """Wiadomość marketingowa idzie kanałem `marketing` z domyślnym priorytetem."""
        payload = {"data": [{"status": "ok", "id": "ticket-a"}]}

        with patch("requests.post", return_value=_response(payload)) as post:
            _send(ExpoPushProvider(), MARKETING_CHANNEL)

        message = post.call_args.kwargs["json"][0]
        assert message["channelId"] == "marketing"
        assert message["priority"] == "default"

    def test_returns_ticket_ids_mapped_to_tokens(self):
        """Adapter zwraca mapę ID ticketu → token dla przyjętych wiadomości."""
        payload = {"data": [{"status": "ok", "id": "ticket-a"}]}

        with patch("requests.post", return_value=_response(payload)):
            result = _send(ExpoPushProvider())

        assert result.tickets == {"ticket-a": "ExponentPushToken[a]"}

    @pytest.mark.parametrize("status_code", [429, 500, 503])
    def test_rate_limit_and_server_errors_are_transient(self, status_code):
        """429 i 5xx to błędy przejściowe — do ponowienia."""
        with patch("requests.post", return_value=_response({}, status_code)):
            with pytest.raises(PushProviderTransientError):
                _send(ExpoPushProvider())

    def test_client_error_is_not_transient(self):
        """400 nie jest ponawiane — to błąd żądania, nie dostawcy."""
        with patch("requests.post", return_value=_response({}, 400)):
            with pytest.raises(PushProviderError) as excinfo:
                _send(ExpoPushProvider())

        assert not isinstance(excinfo.value, PushProviderTransientError)


class TestExpoPushReceipts:
    """Sprawdzanie receiptów Expo."""

    def test_device_not_registered_receipt_returns_token(self):
        """Receipt `DeviceNotRegistered` zwraca token do skasowania."""
        payload = {
            "data": {
                "ticket-a": {"status": "ok"},
                "ticket-b": {
                    "status": "error",
                    "details": {"error": "DeviceNotRegistered"},
                },
            }
        }
        tickets = {
            "ticket-a": "ExponentPushToken[a]",
            "ticket-b": "ExponentPushToken[b]",
        }

        with patch("requests.post", return_value=_response(payload)) as post:
            invalid = ExpoPushProvider().check_receipts(tickets)

        assert invalid == ["ExponentPushToken[b]"]
        assert post.call_args.args[0].endswith("/push/getReceipts")
        assert post.call_args.kwargs["json"] == {"ids": ["ticket-a", "ticket-b"]}

    def test_credentials_error_is_logged_not_deleted(self, caplog):
        """Błąd konfiguracji (`InvalidCredentials`) loguje ERROR i nie kasuje tokenu."""
        payload = {
            "data": {
                "ticket-a": {
                    "status": "error",
                    "details": {"error": "InvalidCredentials"},
                }
            }
        }

        with patch("requests.post", return_value=_response(payload)):
            invalid = ExpoPushProvider().check_receipts(
                {"ticket-a": "ExponentPushToken[a]"}
            )

        assert invalid == []
        assert any(
            record.levelname == "ERROR" and "InvalidCredentials" in record.getMessage()
            for record in caplog.records
        )

    def test_rate_limit_is_transient(self):
        """429 przy receiptach też jest do ponowienia."""
        with patch("requests.post", return_value=_response({}, 429)):
            with pytest.raises(PushProviderTransientError):
                ExpoPushProvider().check_receipts({"ticket-a": "ExponentPushToken[a]"})


@pytest.mark.django_db
class TestPushTasksWithExpoStub:
    """Zadania push na adapterze Expo ze stubem HTTP (eager Celery)."""

    @pytest.fixture(autouse=True)
    def _expo(self, settings):
        settings.PUSH_PROVIDER = EXPO

    def test_rate_limited_send_is_retried(self):
        """429 jest ponawiane — druga próba wysyła push."""
        user = UserFactory()
        PushDevice.objects.create(
            user=user, token="ExponentPushToken[a]", platform="android"
        )
        responses = [
            _response({}, 429),
            _response({"data": [{"status": "ok", "id": "ticket-a"}]}),
            _response({"data": {"ticket-a": {"status": "ok"}}}),
        ]

        with patch("requests.post", side_effect=responses) as post:
            send_push_notification.apply(
                kwargs={
                    "user_id": str(user.pk),
                    "title": "T",
                    "body": "B",
                    "data": {"url": "/orders/X"},
                    "channel": ORDERS_CHANNEL,
                },
                # Eager Celery ponawia od razu i zgłasza `Retry` po fakcie —
                # liczy się, że druga próba poszła.
                throw=False,
            )

        sent = [call for call in post.call_args_list if call.args[0].endswith("/send")]
        assert len(sent) == 2

    def test_receipt_device_not_registered_deletes_device(self):
        """Receipt `DeviceNotRegistered` usuwa urządzenie."""
        user = UserFactory()
        PushDevice.objects.create(
            user=user, token="ExponentPushToken[dead]", platform="android"
        )
        PushDevice.objects.create(
            user=user, token="ExponentPushToken[live]", platform="android"
        )
        payload = {
            "data": {
                "ticket-dead": {
                    "status": "error",
                    "details": {"error": "DeviceNotRegistered"},
                },
                "ticket-live": {"status": "ok"},
            }
        }

        with patch("requests.post", return_value=_response(payload)):
            check_push_receipts.apply(
                kwargs={
                    "tickets": {
                        "ticket-dead": "ExponentPushToken[dead]",
                        "ticket-live": "ExponentPushToken[live]",
                    }
                }
            )

        assert set(PushDevice.objects.values_list("token", flat=True)) == {
            "ExponentPushToken[live]"
        }

    def test_successful_send_schedules_receipt_check(self):
        """Udana wysyłka kolejkuje sprawdzenie receiptów po ~15 minutach."""
        user = UserFactory()
        PushDevice.objects.create(
            user=user, token="ExponentPushToken[a]", platform="android"
        )
        payload = {"data": [{"status": "ok", "id": "ticket-a"}]}

        with (
            patch("requests.post", return_value=_response(payload)),
            patch(
                "apps.notifications.tasks.check_push_receipts.apply_async"
            ) as schedule,
        ):
            send_push_notification.apply(
                kwargs={
                    "user_id": str(user.pk),
                    "title": "T",
                    "body": "B",
                    "channel": ORDERS_CHANNEL,
                }
            )

        schedule.assert_called_once_with(
            kwargs={"tickets": {"ticket-a": "ExponentPushToken[a]"}},
            countdown=15 * 60,
        )


class TestNoopPushProvider:
    """Adapter push, który niczego nie wysyła."""

    def test_sends_nothing(self):
        """Adapter niczego nie wysyła."""
        result = NoopPushProvider().send_push(
            tokens=["ExponentPushToken[a]"],
            title="T",
            body="B",
            data={},
            channel=ORDERS_CHANNEL,
        )

        assert result.invalid_tokens == []
        assert result.tickets == {}
