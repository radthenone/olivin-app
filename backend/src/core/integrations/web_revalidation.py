"""Klient rewalidacji keszu katalogu na webie (ADR 0034, #318).

Backend woła endpoint rewalidacji Next z sekretem i listą tagów. Web
niedostępny to nie katastrofa: strona i tak wygaśnie po kilku minutach,
więc błąd jest logowany, a przejściowy — ponawiany przez zadanie Celery.
"""

from __future__ import annotations

import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

REVALIDATE_PATH = "/api/revalidate"
SECRET_HEADER = "X-Revalidate-Secret"
TIMEOUT_SECONDS = 5


class WebRevalidationTransientError(Exception):
    """Web nie odpowiedział albo zwrócił 429/5xx — rewalidację warto ponowić."""


def revalidate_tags(tags: list[str]) -> bool:
    """Wysyła tagi do rewalidacji; `True`, gdy web je przyjął.

    Bez `REVALIDATE_SECRET` (dev, testy) nic nie wysyła. Odrzucenie 4xx
    (np. zły sekret) to błąd konfiguracji — log, bez ponawiania.
    """
    secret = getattr(settings, "REVALIDATE_SECRET", "")
    if not secret:
        return False
    try:
        response = requests.post(
            f"{settings.FRONTEND_URL}{REVALIDATE_PATH}",
            json={"tags": tags},
            headers={SECRET_HEADER: secret},
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else 0
        if status == 429 or status >= 500:
            raise WebRevalidationTransientError(f"Web HTTP {status}") from exc
        logger.error("Web odrzucił rewalidację %s: HTTP %s", tags, status)
        return False
    except requests.RequestException as exc:
        logger.warning("Web nie odpowiedział na rewalidację %s: %s", tags, exc)
        raise WebRevalidationTransientError(str(exc)) from exc
    return True
