from __future__ import annotations

from typing import Any, Protocol


class PushProviderError(Exception):
    """Dostawca push odmówił albo nie odpowiedział — wysyłka nieskuteczna."""


class PushProvider(Protocol):
    """Kanał push dla powiadomień (`CONTEXT.md`, PushDevice; ADR 0027).

    Interfejs nie zna Expo: przyjmuje tokeny, tytuł, treść i dane, a zwraca
    tokeny odrzucone jako martwe (`DeviceNotRegistered` u Expo). Wywołujący
    kasuje zwrócone tokeny — adapter sam nie tyka bazy.
    """

    def send_push(
        self,
        *,
        tokens: list[str],
        title: str,
        body: str,
        data: dict[str, Any],
    ) -> list[str]:
        """Wysyła push; zwraca tokeny do skasowania (odrzucone przez dostawcę)."""
        ...
