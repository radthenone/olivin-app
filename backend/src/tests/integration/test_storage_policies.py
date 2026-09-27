"""Polityki bucketów na żywym MinIO.

Testy jednostkowe sprawdzają kształt polityki; tutaj sprawdzamy, czy dostawca
faktycznie się nią kieruje. Bez tego „bucket publiczny" jest deklaracją, a nie
faktem — a w tę stronę pomyłka wystawia dokumenty klientów do internetu.
"""

from __future__ import annotations

import urllib.error
import urllib.request
import uuid

import pytest

from core.storage.bucket_manager import S3BucketManager
from core.storage.buckets import ALL_BUCKETS, DOCUMENTS, ORIGINALS, PRODUCTS
from core.storage.utils import sync_buckets

pytestmark = [pytest.mark.integration]


def _fetch(url: str) -> int:
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return response.status
    except urllib.error.HTTPError as error:
        return error.code


@pytest.fixture(scope="module")
def manager() -> S3BucketManager:
    result = sync_buckets()
    assert result.success, result.errors
    return S3BucketManager()


@pytest.fixture
def key() -> str:
    return f"test/{uuid.uuid4()}.txt"


def _put(manager: S3BucketManager, bucket, key: str) -> None:
    manager.client.put_object(Bucket=bucket.name, Key=key, Body=b"olivin")


class TestBucketsExist:
    def test_bootstrap_zaklada_wszystkie_trzy(self, manager: S3BucketManager):
        existing = set(manager.list_buckets())

        assert {bucket.name for bucket in ALL_BUCKETS} <= existing


class TestPublicBucket:
    """`products` — odczyt publiczny, adres bez podpisu."""

    def test_obiekt_jest_do_pobrania_bez_podpisu(
        self, manager: S3BucketManager, key: str
    ):
        _put(manager, PRODUCTS, key)
        endpoint = manager.client.meta.endpoint_url.rstrip("/")

        assert _fetch(f"{endpoint}/{PRODUCTS.name}/{key}") == 200

    def test_polityka_nie_pozwala_wylistowac_zawartosci(self, manager: S3BucketManager):
        endpoint = manager.client.meta.endpoint_url.rstrip("/")

        assert _fetch(f"{endpoint}/{PRODUCTS.name}/") != 200


class TestPrivateBuckets:
    """`originals` i `documents` — bez podpisu nic nie wychodzi."""

    @pytest.mark.parametrize("bucket", [ORIGINALS, DOCUMENTS])
    def test_obiekt_nie_jest_do_pobrania_bez_podpisu(
        self, manager: S3BucketManager, key: str, bucket
    ):
        _put(manager, bucket, key)
        endpoint = manager.client.meta.endpoint_url.rstrip("/")

        assert _fetch(f"{endpoint}/{bucket.name}/{key}") == 403

    @pytest.mark.parametrize("bucket", [ORIGINALS, DOCUMENTS])
    def test_nie_maja_polityki_wpuszczajacej(self, manager: S3BucketManager, bucket):
        assert manager.bucket_policy(bucket.name) is None


class TestSignedUrl:
    """Adres podpisany na czas to jedyna droga do `documents`."""

    def test_podpisany_adres_pobiera_dokument(self, manager: S3BucketManager, key: str):
        _put(manager, DOCUMENTS, key)

        url = manager.presigned_url(DOCUMENTS, key, expires_in=60)

        assert _fetch(url) == 200

    def test_podpisany_adres_wygasa(self, manager: S3BucketManager, key: str):
        _put(manager, DOCUMENTS, key)

        url = manager.presigned_url(DOCUMENTS, key, expires_in=1)

        # Czekanie zastępujemy podpisem, który wygasł, zanim powstał: MinIO
        # sprawdza znacznik czasu, więc efekt jest ten sam, a test nie śpi.
        expired = url.replace("X-Amz-Expires=1&", "X-Amz-Expires=0&")
        assert _fetch(expired) == 403


class TestPolicyIsReappliedOnRestart:
    """Polityka wraca przy każdym starcie, nie tylko przy zakładaniu bucketu."""

    def test_zdjeta_polityka_wraca_po_bootstrapie(self, manager: S3BucketManager):
        manager.client.delete_bucket_policy(Bucket=PRODUCTS.name)
        assert manager.bucket_policy(PRODUCTS.name) is None

        sync_buckets()

        assert manager.bucket_policy(PRODUCTS.name) is not None
