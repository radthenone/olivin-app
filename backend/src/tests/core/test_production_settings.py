"""Produkcja wymaga jawnej domeny webu dla linków z maili (#313, ADR 0038)."""

from __future__ import annotations

import runpy
from pathlib import Path

import pytest
from django.core.exceptions import ImproperlyConfigured

import core.settings

PRODUCTION = Path(core.settings.__file__).with_name("production.py")


class TestProductionFrontendUrl:
    """Brak `FRONTEND_URL` w produkcji zatrzymuje start zamiast linków na localhost."""

    def test_missing_frontend_url_raises(self, monkeypatch: pytest.MonkeyPatch):
        """Bez `FRONTEND_URL` ustawienia produkcyjne rzucają ImproperlyConfigured."""
        monkeypatch.delenv("FRONTEND_URL", raising=False)

        with pytest.raises(ImproperlyConfigured, match="FRONTEND_URL"):
            runpy.run_path(str(PRODUCTION))

    def test_frontend_url_set_loads(self, monkeypatch: pytest.MonkeyPatch):
        """Ustawione `FRONTEND_URL` → ustawienia produkcyjne ładują się."""
        monkeypatch.setenv("FRONTEND_URL", "https://olivin.example")

        assert runpy.run_path(str(PRODUCTION))["DEBUG"] is False
