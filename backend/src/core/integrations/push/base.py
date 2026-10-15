from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

# Kanały Androida (ADR 0037): transakcyjne z wysokim priorytetem, marketing
# z domyślnym — klient wycisza marketing w systemie, nie tracąc statusów.
ORDERS_CHANNEL = "orders"
MARKETING_CHANNEL = "marketing"


class PushProviderError(Exception):
    """Dostawca push odmówił albo nie odpowiedział — wysyłka nieskuteczna."""


class PushProviderTransientError(PushProviderError):
    """Błąd przejściowy (sieć, 429, 5xx) — wysyłkę warto ponowić z odstępem."""


@dataclass(frozen=True)
class PushResult:
    """Wynik wysyłki: tokeny martwe od razu i tickety do sprawdzenia receiptów."""

    invalid_tokens: list[str] = field(default_factory=list)
    # ID ticketu dostawcy → token; receipt sprawdzany później (`check_receipts`).
    tickets: dict[str, str] = field(default_factory=dict)


class PushProvider(Protocol):
    """Kanał push dla powiadomień (`CONTEXT.md`, PushDevice; ADR 0027, 0037).

    Interfejs nie zna Expo: przyjmuje tokeny, tytuł, treść, dane i kanał,
    a zwraca tokeny odrzucone jako martwe (`DeviceNotRegistered` u Expo)
    oraz tickety do późniejszego sprawdzenia doręczenia. Wywołujący kasuje
    zwrócone tokeny — adapter sam nie tyka bazy.
    """

    def send_push(
        self,
        *,
        tokens: list[str],
        title: str,
        body: str,
        data: dict[str, Any],
        channel: str,
    ) -> PushResult:
        """Wysyła push; zwraca tokeny do skasowania i tickety do receiptów."""
        ...

    def check_receipts(self, tickets: dict[str, str]) -> list[str]:
        """Sprawdza receipty ticketów; zwraca tokeny do skasowania."""
        ...
