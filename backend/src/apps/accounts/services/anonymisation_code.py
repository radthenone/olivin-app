"""Kod potwierdzenia anonimizacji dla konta bez hasła (logowanie społecznościowe).

Kod trzymany w cache'u jako HMAC, nie jawnie; po `MAX_ATTEMPTS` błędnych
próbach przepada i trzeba poprosić o nowy.
"""

from __future__ import annotations

import secrets

from django.core.cache import cache
from django.db import transaction
from django.utils.crypto import constant_time_compare, salted_hmac

from apps.accounts.models import CustomUser
from core.integrations.notifications.mail import send_notification_email

CODE_TIMEOUT = 15 * 60
RESEND_COOLDOWN = 60
MAX_ATTEMPTS = 5
_SALT = "account-anonymisation-code"


def _key(user: CustomUser, suffix: str) -> str:
    return f"account-anonymisation:{user.pk}:{suffix}"


def _digest(code: str) -> str:
    return salted_hmac(_SALT, code).hexdigest()


def send_code(user: CustomUser) -> None:
    """Wysyła 6-cyfrowy kod na adres konta — najwyżej raz na `RESEND_COOLDOWN`."""
    if not cache.add(_key(user, "cooldown"), True, timeout=RESEND_COOLDOWN):
        return
    code = f"{secrets.randbelow(1_000_000):06d}"
    cache.set(_key(user, "code"), _digest(code), timeout=CODE_TIMEOUT)
    cache.set(_key(user, "attempts"), 0, timeout=CODE_TIMEOUT)
    to = user.email
    transaction.on_commit(
        lambda: send_notification_email(
            to=to,
            subject="Kod potwierdzenia usunięcia konta",
            body=(
                f"Twój kod potwierdzenia usunięcia konta: {code}\n\n"
                "Kod jest ważny 15 minut. Jeśli to nie Ty, zignoruj tę "
                "wiadomość i zmień zabezpieczenia konta."
            ),
        ),
        robust=True,
    )


def verify_code(user: CustomUser, code: str) -> bool:
    """Sprawdza kod; poprawny jest jednorazowy, błędne liczą się do limitu."""
    expected = cache.get(_key(user, "code"))
    if expected is None:
        return False
    if constant_time_compare(expected, _digest(code)):
        cache.delete_many([_key(user, "code"), _key(user, "attempts")])
        return True
    try:
        attempts = cache.incr(_key(user, "attempts"))
    except ValueError:
        attempts = MAX_ATTEMPTS
    if attempts >= MAX_ATTEMPTS:
        cache.delete(_key(user, "code"))
    return False
