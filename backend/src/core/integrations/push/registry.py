from __future__ import annotations

from django.conf import settings
from django.utils.module_loading import import_string

from core.integrations.push.base import PushProvider

DEFAULT_PROVIDER = "core.integrations.push.noop.NoopPushProvider"


def get_provider() -> PushProvider:
    """Dostawca push wskazany konfiguracją.

    Domyślnie donikąd: dev/test nie wysyłają nic bez jawnej konfiguracji
    produkcyjnej na Expo. Pomyłka w konfiguracji kosztuje brak pusha,
    nie wyciek powiadomień do obcego dostawcy.
    """
    path = getattr(settings, "PUSH_PROVIDER", DEFAULT_PROVIDER)
    return import_string(path)()
