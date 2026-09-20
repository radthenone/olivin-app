"""Silnik tłumaczeń na potrzeby testów.

Produkcja ma DeepL albo LibreTranslate; testy mają to. Chodzi o to, żeby
zachowanie było przewidywalne i żeby suita nie potrzebowała sieci — a nie
o jakość przekładu, której i tak nie sprawdzamy.
"""

from __future__ import annotations

PREFIX = "EN "


class StubProvider:
    """Doklejka do tekstu, żeby po wyniku było widać, że przeszedł silnik.

    Prefiks jest oddzielony spacją, bo wynik bywa zamieniany na slug —
    „EN Gold rings" daje `en-gold-rings`, czyli coś, co da się przeczytać
    w asercji.
    """

    def translate(
        self, texts: list[str], *, target_language: str, source_language: str
    ) -> list[str]:
        return [f"{PREFIX}{text}" for text in texts]


class BrokenProvider:
    """Silnik, który nie odpowiada — do testów odmowy zapisu."""

    def translate(
        self, texts: list[str], *, target_language: str, source_language: str
    ) -> list[str]:
        raise ConnectionError("silnik tłumaczeń nie odpowiada")
