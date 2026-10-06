from __future__ import annotations

from typing import Any


class NoopPushProvider:
    """Atrapa „donikąd” na dev/test — nic nie wysyła (issue #202).

    Domyślny dostawca, żeby robocze uruchomienie bez klucza Expo nie
    próbowało uderzać w sieć. Produkcja wskazuje Expo jawną konfiguracją.
    """

    def send_push(
        self,
        *,
        tokens: list[str],
        title: str,
        body: str,
        data: dict[str, Any],
    ) -> list[str]:
        return []
