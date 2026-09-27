"""Konfiguracja cache'u.

Cache jest współdzielony, a nie procesowy, bo trzyma stan, który musi być
wspólny dla wszystkich procesów aplikacji: historię żądań dla limitów DRF.
Na pamięci lokalnej limit „60 na minutę” mnoży się przez liczbę workerów
i zeruje przy każdym restarcie.
"""

import os

REDIS_CACHE_URL = str(os.environ.get("REDIS_CACHE_URL", "redis://olivin-redis:6379/1"))

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_CACHE_URL,
    }
}
