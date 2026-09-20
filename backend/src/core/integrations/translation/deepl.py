from __future__ import annotations

import requests
from django.conf import settings

API_URL = "https://api-free.deepl.com/v2/translate"
TIMEOUT_SECONDS = 20


class DeepLProvider:
    """DeepL przez jego API tekstowe — dostawca produkcyjny (ADR 0027).

    Bez pakietu `deepl`: jedno wywołanie HTTP nie wymaga biblioteki, a ta
    dołożyłaby zależność, której i tak nie da się uruchomić w ciągłej
    integracji bez klucza.
    """

    def __init__(self, api_key: str | None = None, api_url: str | None = None):
        self.api_key = api_key or getattr(settings, "DEEPL_API_KEY", "")
        self.api_url = api_url or getattr(settings, "DEEPL_API_URL", API_URL)

    def translate(
        self,
        texts: list[str],
        *,
        target_language: str,
        source_language: str,
    ) -> list[str]:
        if not texts:
            return []
        if not self.api_key:
            raise RuntimeError(
                "Brak klucza DeepL — ustaw DEEPL_API_KEY albo wybierz innego "
                "dostawcę przez TRANSLATION_PROVIDER."
            )

        response = requests.post(
            self.api_url,
            headers={"Authorization": f"DeepL-Auth-Key {self.api_key}"},
            data={
                "text": texts,
                "target_lang": target_language.upper(),
                "source_lang": source_language.upper(),
            },
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return [item["text"] for item in response.json()["translations"]]
