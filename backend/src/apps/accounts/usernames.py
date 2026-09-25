"""Nazwa użytkownika: generowanie `anon<liczba>` i reguły nazwy wybranej przez klienta.

Moduł poza `services/`, bo korzysta z niego model `CustomUser` (pakiet `services`
importuje modele — byłby cykl).
"""

import secrets

from django.core.validators import RegexValidator

ANON_USERNAME_PREFIX = "anon"
# 8 cyfr: ~90 mln wartości, kolizja rzadka; i tak ponawiamy przy zajętej nazwie.
ANON_USERNAME_MIN = 10_000_000
ANON_USERNAME_SPAN = 90_000_000
ANON_USERNAME_MAX_ATTEMPTS = 10

USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 30
username_chars_validator = RegexValidator(
    r"^[A-Za-z0-9._-]+$",
    "Nazwa może zawierać tylko litery a-z, cyfry oraz znaki . _ -",
)


def generate_anon_username() -> str:
    """Losuje kandydata `anon<liczba>`; unikalność sprawdza zapis modelu."""
    return f"{ANON_USERNAME_PREFIX}{ANON_USERNAME_MIN + secrets.randbelow(ANON_USERNAME_SPAN)}"
