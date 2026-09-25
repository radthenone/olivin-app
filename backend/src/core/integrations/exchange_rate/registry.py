from __future__ import annotations

from django.conf import settings
from django.utils.module_loading import import_string

from core.integrations.exchange_rate.base import ExchangeRateProvider

DEFAULT_PROVIDER = "core.integrations.exchange_rate.nbp.NbpProvider"


def get_provider() -> ExchangeRateProvider:
    """Dostawca kursu walut wskazany przez `EXCHANGE_RATE_PROVIDER`."""
    path = getattr(settings, "EXCHANGE_RATE_PROVIDER", DEFAULT_PROVIDER)
    return import_string(path)()
