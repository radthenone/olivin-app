from __future__ import annotations

from django.conf import settings
from django.utils.module_loading import import_string

from core.integrations.translation.base import TranslationProvider

DEFAULT_PROVIDER = "core.integrations.translation.libre.LibreTranslateProvider"


def get_provider() -> TranslationProvider:
    """Silnik tłumaczenia wskazany konfiguracją.

    Domyślnie deweloperski: produkcja wskazuje DeepL jawnie, a pomyłka
    w konfiguracji ma kosztować gorsze tłumaczenie, nie rachunek u dostawcy.
    """
    path = getattr(settings, "TRANSLATION_PROVIDER", DEFAULT_PROVIDER)
    return import_string(path)()
