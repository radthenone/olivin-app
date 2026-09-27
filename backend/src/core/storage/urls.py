"""Składanie adresów z klucza obiektu.

Model trzyma sam klucz (ADR 0025), więc adres powstaje dopiero przy
serializacji — i zależy od tego, czy bucket jest publiczny, czy prywatny.
Obie drogi idą przez tę samą klasę magazynu, żeby host i nazwa bucketa
były składane w jednym miejscu.
"""

from __future__ import annotations

from core.storage.buckets import DEFAULT_URL_TTL_SECONDS, Bucket
from core.storage.storages import storage_for


def object_url(
    bucket: Bucket,
    key: str,
    expires_in: int = DEFAULT_URL_TTL_SECONDS,
) -> str:
    """Adres obiektu: stały dla bucketa publicznego, podpisany dla prywatnego."""
    storage = storage_for(bucket)
    if bucket.is_public:
        return storage.url(key)
    return storage.url(key, expire=expires_in)
