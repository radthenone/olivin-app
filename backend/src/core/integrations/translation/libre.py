from __future__ import annotations

import requests
from django.conf import settings

API_URL = "http://olivin-libretranslate:5000/translate"
TIMEOUT_SECONDS = 30


class LibreTranslateProvider:
    """LibreTranslate — silnik deweloperski (ADR 0027).

    Uruchamiany obok aplikacji z `LT_LOAD_ONLY=pl,en`, żeby kontener nie
    ciągnął modeli wszystkich języków. Tłumaczy gorzej niż DeepL i o to
    chodzi: w środowisku roboczym liczy się, że w ogóle odpowiada.
    """

    def __init__(self, api_url: str | None = None, api_key: str | None = None):
        self.api_url = api_url or getattr(settings, "LIBRETRANSLATE_URL", API_URL)
        self.api_key = api_key or getattr(settings, "LIBRETRANSLATE_API_KEY", "")

    def translate(
        self,
        texts: list[str],
        *,
        target_language: str,
        source_language: str,
    ) -> list[str]:
        if not texts:
            return []

        payload: dict = {
            "q": texts,
            "source": source_language,
            "target": target_language,
            "format": "text",
        }
        if self.api_key:
            payload["api_key"] = self.api_key

        response = requests.post(self.api_url, json=payload, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        translated = response.json()["translatedText"]
        # Przy jednym tekście LibreTranslate odpowiada łańcuchem, nie listą.
        return translated if isinstance(translated, list) else [translated]
