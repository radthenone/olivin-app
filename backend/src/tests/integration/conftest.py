from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def mock_s3_storage():
    """Wyłącza globalny mock S3 — testy integracyjne mają używać prawdziwego MinIO/S3."""

    yield


@pytest.fixture(autouse=True)
def mock_redis_connection():
    """Wyłącza globalny mock Redis — testy integracyjne mają używać prawdziwego Redis."""

    yield
