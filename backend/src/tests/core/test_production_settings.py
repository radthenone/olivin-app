"""Produkcja wymaga jawnych adresów webu i API oraz sekretu rewalidacji (#313, #314, #318)."""

from __future__ import annotations

import runpy
from pathlib import Path

import pytest
from django.core.exceptions import ImproperlyConfigured

import core.settings

PRODUCTION = Path(core.settings.__file__).with_name("production.py")


@pytest.fixture(autouse=True)
def revalidate_secret(monkeypatch: pytest.MonkeyPatch):
    """Sekret rewalidacji ustawiony — testy adresów sprawdzają tylko adresy."""
    monkeypatch.setenv("REVALIDATE_SECRET", "prod-secret")


class TestProductionFrontendUrl:
    """Brak `FRONTEND_URL` w produkcji zatrzymuje start zamiast linków na localhost."""

    def test_missing_frontend_url_raises(self, monkeypatch: pytest.MonkeyPatch):
        """Bez `FRONTEND_URL` ustawienia produkcyjne rzucają ImproperlyConfigured."""
        monkeypatch.delenv("FRONTEND_URL", raising=False)
        monkeypatch.setenv("BACKEND_URL", "https://api.olivin.example")

        with pytest.raises(ImproperlyConfigured, match="FRONTEND_URL"):
            runpy.run_path(str(PRODUCTION))

    def test_frontend_url_set_loads(self, monkeypatch: pytest.MonkeyPatch):
        """Ustawione `FRONTEND_URL` → ustawienia produkcyjne ładują się."""
        monkeypatch.setenv("FRONTEND_URL", "https://olivin.example")
        monkeypatch.setenv("BACKEND_URL", "https://api.olivin.example")

        assert runpy.run_path(str(PRODUCTION))["DEBUG"] is False


class TestProductionBackendUrl:
    """Brak `BACKEND_URL` w produkcji zatrzymuje start (nagłówek RFC 8058, #314)."""

    def test_missing_backend_url_raises(self, monkeypatch: pytest.MonkeyPatch):
        """Bez `BACKEND_URL` ustawienia produkcyjne rzucają ImproperlyConfigured."""
        monkeypatch.setenv("FRONTEND_URL", "https://olivin.example")
        monkeypatch.delenv("BACKEND_URL", raising=False)

        with pytest.raises(ImproperlyConfigured, match="BACKEND_URL"):
            runpy.run_path(str(PRODUCTION))

    def test_plain_http_backend_url_raises(self, monkeypatch: pytest.MonkeyPatch):
        """`BACKEND_URL` bez HTTPS rzuca — RFC 8058 wymaga HTTPS, a POST po 301 ginie."""
        monkeypatch.setenv("FRONTEND_URL", "https://olivin.example")
        monkeypatch.setenv("BACKEND_URL", "http://api.olivin.example")

        with pytest.raises(ImproperlyConfigured, match="BACKEND_URL"):
            runpy.run_path(str(PRODUCTION))


class TestProductionRevalidateSecret:
    """Brak `REVALIDATE_SECRET` w produkcji ostrzega, ale nie blokuje startu (#318).

    Route `/api/revalidate` po stronie webu jeszcze nie istnieje; wymóg wróci
    razem z nim.
    """

    def test_missing_revalidate_secret_warns(self, monkeypatch: pytest.MonkeyPatch):
        """Bez sekretu ustawienia ładują się z ostrzeżeniem o wyłączonej rewalidacji."""
        monkeypatch.setenv("FRONTEND_URL", "https://olivin.example")
        monkeypatch.setenv("BACKEND_URL", "https://api.olivin.example")
        monkeypatch.delenv("REVALIDATE_SECRET", raising=False)

        with pytest.warns(RuntimeWarning, match="REVALIDATE_SECRET"):
            assert runpy.run_path(str(PRODUCTION))["DEBUG"] is False
