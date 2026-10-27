"""Widoki headless logowania kodem z limitem żądań jako 429 (#407).

Allauth zgłasza przekroczenie limitu zamówienia kodu jako błąd walidacji (400),
a potwierdzenie kodu nie ma własnego limitu — kończy się błędem kodu albo
konfliktem. Klient web i mobile rozpoznaje limit po statusie 429, więc oba
widoki podmieniamy na własne.
"""

from __future__ import annotations

from typing import Any

from allauth.core import ratelimit
from allauth.headless.account.views import (
    ConfirmLoginCodeView as AllauthConfirmLoginCodeView,
    RequestLoginCodeView as AllauthRequestLoginCodeView,
)
from allauth.headless.base.response import RateLimitResponse
from django.http import HttpRequest, HttpResponseBase

TOO_MANY_LOGIN_ATTEMPTS = "too_many_login_attempts"


class RequestLoginCodeView(AllauthRequestLoginCodeView):
    """Zamówienie kodu: przekroczenie limitu zwraca 429, nie 400."""

    def handle_invalid_input(self, input: Any) -> HttpResponseBase:
        """Limit prób allauth zamienia na odpowiedź 429."""
        if _has_error_code(input, TOO_MANY_LOGIN_ATTEMPTS):
            return RateLimitResponse(self.request)
        return super().handle_invalid_input(input)


class ConfirmLoginCodeView(AllauthConfirmLoginCodeView):
    """Potwierdzenie kodu: każde podejście liczy się do limitu `login_by_code`."""

    process: Any

    def handle(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        """Odrzuca potwierdzenia ponad limit dla adresu z zaczętego logowania."""
        state = self.process.state
        key = (state.get("email") or state.get("phone") or "").lower()
        limited = ratelimit.consume_or_429(request, action="login_by_code", key=key)
        if limited:
            return limited
        return super().handle(request, *args, **kwargs)


def _has_error_code(input: Any, code: str) -> bool:
    """Czy formularz allauth odrzucił żądanie właśnie tym kodem błędu."""
    return any(
        error.code == code
        for field_errors in input.errors.values()
        for error in field_errors.as_data()
    )
