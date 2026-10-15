"""Preferowany język klienta dla maili (`CONTEXT.md`, PreferredLanguage; ADR 0035)."""

from __future__ import annotations

from django.conf import settings
from django.db import models
from django.http import HttpRequest
from django.utils.translation.trans_real import parse_accept_lang_header
from rest_framework.request import Request


class PreferredLanguage(models.TextChoices):
    """Język maili; brak wartości oznacza polski."""

    PL = "pl", "Polski"
    EN = "en", "Angielski"


def language_from_request(request: HttpRequest | Request) -> str | None:
    """Język z `Accept-Language`: `pl*` → `pl`, każdy inny → `en`, brak → `None`."""
    parsed = parse_accept_lang_header(request.META.get("HTTP_ACCEPT_LANGUAGE", ""))
    if not parsed:
        return None
    # Wynik jest posortowany po wadze `q` — pierwszy to język najbardziej chciany.
    tag = parsed[0][0]
    return PreferredLanguage.PL if tag.startswith("pl") else PreferredLanguage.EN


def email_language(source: object) -> str:
    """Język maila dla odbiorcy: konto, zamówienie albo subskrypcja newslettera.

    Konto (także właściciel zamówienia) bierze język z profilu, zamówienie
    gościa i subskrypcja — z własnego `preferred_language`. Brak → `pl`.
    """
    owner = getattr(source, "user", None) or source
    # Brak profilu rzuca `RelatedObjectDoesNotExist` (podklasa `AttributeError`).
    holder = getattr(owner, "profile", owner)
    value = getattr(holder, "preferred_language", None)
    return (
        PreferredLanguage.EN if value == PreferredLanguage.EN else PreferredLanguage.PL
    )


def localized_link(url: str, language: str) -> str:
    """Podmienia prefiks `/pl` linku sklepu (`FRONTEND_LINK_BASE`) na język odbiorcy."""
    base = settings.FRONTEND_LINK_BASE
    if language == PreferredLanguage.PL or not url.startswith(f"{base}/"):
        return url
    return f"{settings.FRONTEND_URL}/{language}{url[len(base) :]}"
