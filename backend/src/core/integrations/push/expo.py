from __future__ import annotations

from typing import Any

import requests
from django.conf import settings

from core.integrations.push.base import PushProviderError

API_URL = "https://exp.host/--/api/v2/push/send"
TIMEOUT_SECONDS = 15

# Błąd Expo oznaczający martwy token — urządzenie do skasowania (issue #202).
DEVICE_NOT_REGISTERED = "DeviceNotRegistered"


class ExpoPushProvider:
    """Dostawca push przez usługę Expo (ADR 0027).

    Nazwy pól Expo (`to`, `title`, `body`, `data`) zostają w adapterze —
    serwis powiadomień operuje na tokenach i treści, nie na protokole Expo.
    Odpowiedź Expo to lista wyników w tej samej kolejności co żądania:
    `status: ok` albo `status: error` ze szczegółem `details.error`.
    """

    def __init__(self, api_url: str | None = None, access_token: str | None = None):
        self.api_url = api_url or getattr(settings, "EXPO_PUSH_URL", API_URL)
        self.access_token = access_token or getattr(settings, "EXPO_ACCESS_TOKEN", "")

    def send_push(
        self,
        *,
        tokens: list[str],
        title: str,
        body: str,
        data: dict[str, Any],
    ) -> list[str]:
        """Wysyła push przez Expo; zwraca tokeny odrzucone jako niezarejestrowane."""
        if not tokens:
            return []
        messages = [
            {"to": token, "title": title, "body": body, "data": data}
            for token in tokens
        ]
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        try:
            response = requests.post(
                self.api_url,
                json=messages,
                headers=headers,
                timeout=TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException as exc:
            raise PushProviderError(f"Expo nie odpowiedziało: {exc}") from exc
        results = payload.get("data", [])
        invalid: list[str] = []
        for token, result in zip(tokens, results):
            if isinstance(result, dict) and result.get("status") == "error":
                details = result.get("details") or {}
                if details.get("error") == DEVICE_NOT_REGISTERED:
                    invalid.append(token)
        return invalid
