"""Ładowanie plików `.env` w `core/envs.py`."""

from __future__ import annotations

import os

import pytest

from core import envs

PROBE = "OLIVIN_ENVS_PROBE"


@pytest.fixture
def project_with_dev_env(tmp_path, monkeypatch):
    """Katalog projektu z plikiem `.envs/dev`, który ustawia zmienną-sondę."""
    backend_envs = tmp_path / ".envs/dev/backend"
    backend_envs.mkdir(parents=True)
    (backend_envs / "s3.env").write_text(f"{PROBE}=from-dev-env\n")
    monkeypatch.setattr(envs, "PROJECT_DIR", tmp_path)
    # setenv + delenv: monkeypatch zapamięta brak zmiennej i sprzątnie to,
    # co wpisze `load_dotenv`.
    monkeypatch.setenv(PROBE, "placeholder")
    monkeypatch.delenv(PROBE)
    return tmp_path


class TestLoadValidEnvs:
    """Wybór plików `.envs` zależy od `DJANGO_ENVIRONMENT`, tak jak ustawienia."""

    def test_testing_skips_dev_env_files(self, project_with_dev_env, monkeypatch):
        """W testach pliki `.envs/dev` nie są czytane — wynik nie zależy od maszyny."""
        monkeypatch.setenv("DJANGO_ENVIRONMENT", "testing")

        envs.load_valid_envs()

        assert PROBE not in os.environ

    def test_development_loads_dev_env_files(self, project_with_dev_env, monkeypatch):
        """W środowisku roboczym pliki `.envs/dev` dalej są ładowane."""
        monkeypatch.setenv("DJANGO_ENVIRONMENT", "development")

        envs.load_valid_envs()

        assert os.environ[PROBE] == "from-dev-env"

    def test_legacy_django_env_is_ignored(self, project_with_dev_env, monkeypatch):
        """Martwe `DJANGO_ENV` nie przełącza ładowania — źródłem prawdy jest `DJANGO_ENVIRONMENT`."""
        monkeypatch.setenv("DJANGO_ENVIRONMENT", "testing")
        monkeypatch.setenv("DJANGO_ENV", "dev")

        envs.load_valid_envs()

        assert PROBE not in os.environ
