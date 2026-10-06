from __future__ import annotations

from typing import Any, ClassVar


class FakePushProvider:
    """Atrapa kanału push do testów (issue #202).

    Zapisuje wysyłki na poziomie klasy, bo rejestr tworzy nowy obiekt przy
    każdym wywołaniu. `invalid_tokens` udaje odrzucenie przez Expo —
    następna wysyłka zwróci je jako martwe do skasowania.
    """

    sent: ClassVar[list[dict[str, Any]]] = []
    invalid_tokens: ClassVar[list[str]] = []
    fail_with: ClassVar[str] = ""

    @classmethod
    def reset(cls) -> None:
        cls.sent = []
        cls.invalid_tokens = []
        cls.fail_with = ""

    def send_push(
        self,
        *,
        tokens: list[str],
        title: str,
        body: str,
        data: dict[str, Any],
    ) -> list[str]:
        from core.integrations.push.base import PushProviderError

        if self.fail_with:
            raise PushProviderError(self.fail_with)
        self.sent.append(
            {"tokens": list(tokens), "title": title, "body": body, "data": dict(data)}
        )
        invalid = [token for token in tokens if token in self.invalid_tokens]
        return invalid
