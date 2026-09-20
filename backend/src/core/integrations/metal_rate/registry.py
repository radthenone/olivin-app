from __future__ import annotations

from django.conf import settings
from django.utils.module_loading import import_string

from core.integrations.metal_rate.base import MetalRateProvider

DEFAULT_PROVIDER = "core.integrations.metal_rate.last_active.LastActiveRateProvider"


def get_provider() -> MetalRateProvider:
    """Dostawca notowań wskazany konfiguracją.

    Wybór jest ustawieniem, a nie importem w miejscu użycia: zamiana dostawcy
    po rozstrzygnięciu ADR 0027 ma być zmianą jednej wartości.
    """
    path = getattr(settings, "METAL_RATE_PROVIDER", DEFAULT_PROVIDER)
    return import_string(path)()
