from __future__ import annotations

import logging
from typing import Any

import requests
from django.conf import settings

from core.integrations.push.base import (
    ORDERS_CHANNEL,
    PushProviderError,
    PushProviderTransientError,
    PushResult,
)

logger = logging.getLogger(__name__)

API_URL = "https://exp.host/--/api/v2/push/send"
TIMEOUT_SECONDS = 15

# Błąd Expo oznaczający martwy token — urządzenie do skasowania (issue #202).
DEVICE_NOT_REGISTERED = "DeviceNotRegistered"
# Błędy konfiguracji po naszej stronie — alert dla nas, nie wina tokenu.
CONFIGURATION_ERRORS = frozenset({"InvalidCredentials", "MismatchSenderId"})


class ExpoPushProvider:
    """Dostawca push przez usługę Expo (ADR 0027, 0037).

    Nazwy pól Expo (`to`, `channelId`, `priority`...) zostają w adapterze —
    serwis powiadomień operuje na tokenach, treści i kanale, nie na protokole
    Expo. Odpowiedź wysyłki to lista ticketów w kolejności żądań: `status: ok`
    z `id` albo `status: error` ze szczegółem `details.error`. Ticket `ok`
    znaczy tylko „przyjęte przez Expo” — doręczenie potwierdza receipt
    (`check_receipts`), sprawdzany około 15 minut później.
    """

    def __init__(self, api_url: str | None = None, access_token: str | None = None):
        self.api_url = api_url or getattr(settings, "EXPO_PUSH_URL", API_URL)
        self.access_token = access_token or getattr(settings, "EXPO_ACCESS_TOKEN", "")

    @property
    def receipts_url(self) -> str:
        return self.api_url.rsplit("/", 1)[0] + "/getReceipts"

    def _post(self, url: str, payload: Any) -> dict[str, Any]:
        """POST do Expo; 429, 5xx i błąd sieci → błąd przejściowy (do ponowienia)."""
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        try:
            response = requests.post(
                url, json=payload, headers=headers, timeout=TIMEOUT_SECONDS
            )
            response.raise_for_status()
            payload = response.json()
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else 0
            if status == 429 or status >= 500:
                raise PushProviderTransientError(f"Expo HTTP {status}") from exc
            raise PushProviderError(f"Expo odrzuciło żądanie: {exc}") from exc
        except requests.ReadTimeout as exc:
            # Expo mogło już przyjąć paczkę — ponowienie dałoby duplikat pusha,
            # a duplikat jest gorszy niż jeden zgubiony.
            raise PushProviderError(f"Expo nie odpowiedziało w czasie: {exc}") from exc
        except requests.RequestException as exc:
            raise PushProviderTransientError(f"Expo nie odpowiedziało: {exc}") from exc
        if not isinstance(payload, dict):
            return {}
        if payload.get("errors"):
            # HTTP 200 z błędem całego żądania (np. `PUSH_TOO_MANY_NOTIFICATIONS`).
            logger.error("Expo odrzuciło żądanie: %s", payload.get("errors"))
        return payload

    def send_push(
        self,
        *,
        tokens: list[str],
        title: str,
        body: str,
        data: dict[str, Any],
        channel: str,
    ) -> PushResult:
        """Wysyła push przez Expo; zwraca martwe tokeny i tickety do receiptów."""
        if not tokens:
            return PushResult()
        # Bez `sound` iOS dostarcza po cichu; Android `normal` bywa opóźniany
        # na uśpionym urządzeniu — transakcyjne idą z `high`.
        priority = "high" if channel == ORDERS_CHANNEL else "default"
        messages = [
            {
                "to": token,
                "title": title,
                "body": body,
                "data": data,
                "channelId": channel,
                "priority": priority,
                "sound": "default",
            }
            for token in tokens
        ]
        results = self._post(self.api_url, messages).get("data", [])
        invalid: list[str] = []
        tickets: dict[str, str] = {}
        for token, result in zip(tokens, results):
            if not isinstance(result, dict):
                continue
            if result.get("status") == "ok" and result.get("id"):
                tickets[result["id"]] = token
            elif result.get("status") == "error":
                # ponytail: `MessageRateExceeded` w tickecie nie jest ponawiane
                # (poza #315) — ponawianie per token, gdy pojawi się w logach.
                details = result.get("details") or {}
                if details.get("error") == DEVICE_NOT_REGISTERED:
                    invalid.append(token)
        return PushResult(invalid_tokens=invalid, tickets=tickets)

    def check_receipts(self, tickets: dict[str, str]) -> list[str]:
        """Sprawdza receipty; zwraca tokeny z `DeviceNotRegistered`.

        Błędy konfiguracji (`InvalidCredentials`, `MismatchSenderId`) idą do
        logu na poziomie ERROR — token jest w porządku, zepsuty jest klucz.
        """
        if not tickets:
            return []
        # ponytail: jedno żądanie — Expo przyjmuje do 1000 ID, a wysyłka
        # jest per klient; paczkowanie, gdy pojawi się masowa wysyłka.
        receipts = self._post(self.receipts_url, {"ids": list(tickets)}).get("data", {})
        if not isinstance(receipts, dict):
            return []
        invalid: list[str] = []
        for ticket_id, receipt in receipts.items():
            if not isinstance(receipt, dict) or receipt.get("status") != "error":
                continue
            error = (receipt.get("details") or {}).get("error")
            if error == DEVICE_NOT_REGISTERED and ticket_id in tickets:
                invalid.append(tickets[ticket_id])
            elif error in CONFIGURATION_ERRORS:
                logger.error("Expo receipt %s: błąd konfiguracji %s", ticket_id, error)
        return invalid
