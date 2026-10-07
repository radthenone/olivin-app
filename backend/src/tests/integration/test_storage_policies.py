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
    """Menedżer bucketów połączony z prawdziwym MinIO."""
    result = sync_buckets()
    assert result.success, result.errors
    return S3BucketManager()


@pytest.fixture
def key() -> str:
    """Unikalny klucz obiektu testowego."""
    return f"test/{uuid.uuid4()}.txt"


def _put(manager: S3BucketManager, bucket, key: str) -> None:
    manager.client.put_object(Bucket=bucket.name, Key=key, Body=b"olivin")


class TestBucketsExist:
    """Bootstrap zakłada buckety w MinIO."""

    def test_bootstrap_creates_all_three(self, manager: S3BucketManager):
        """Bootstrap zakłada wszystkie trzy buckety."""
        existing = set(manager.list_buckets())

        assert {bucket.name for bucket in ALL_BUCKETS} <= existing


class TestPublicBucket:
    """`products` — odczyt publiczny, adres bez podpisu."""

    def test_object_is_downloadable_without_signature(
        self, manager: S3BucketManager, key: str
    ):
        """Obiekt da się pobrać bez podpisu."""
        _put(manager, PRODUCTS, key)
        endpoint = manager.client.meta.endpoint_url.rstrip("/")

        assert _fetch(f"{endpoint}/{PRODUCTS.name}/{key}") == 200

    def test_policy_does_not_allow_listing(self, manager: S3BucketManager):
        """Polityka nie pozwala wylistować zawartości."""
        endpoint = manager.client.meta.endpoint_url.rstrip("/")

        assert _fetch(f"{endpoint}/{PRODUCTS.name}/") != 200


class TestPrivateBuckets:
    """`originals` i `documents` — bez podpisu nic nie wychodzi."""

    @pytest.mark.parametrize("bucket", [ORIGINALS, DOCUMENTS])
    def test_object_is_not_downloadable_without_signature(
        self, manager: S3BucketManager, key: str, bucket
    ):
        """Obiektu nie da się pobrać bez podpisu."""
        _put(manager, bucket, key)
        endpoint = manager.client.meta.endpoint_url.rstrip("/")

        assert _fetch(f"{endpoint}/{bucket.name}/{key}") == 403

    @pytest.mark.parametrize("bucket", [ORIGINALS, DOCUMENTS])
    def test_have_no_public_policy(self, manager: S3BucketManager, bucket):
        """Prywatne buckety nie mają polityki wpuszczającej."""
        assert manager.bucket_policy(bucket.name) is None


class TestSignedUrl:
    """Adres podpisany na czas to jedyna droga do `documents`."""

    def test_signed_url_downloads_document(self, manager: S3BucketManager, key: str):
        """Podpisany adres pobiera dokument."""
        _put(manager, DOCUMENTS, key)

        url = manager.presigned_url(DOCUMENTS, key, expires_in=60)

        assert _fetch(url) == 200

    def test_signed_url_expires(self, manager: S3BucketManager, key: str):
        """Podpisany adres wygasa."""
        _put(manager, DOCUMENTS, key)

        url = manager.presigned_url(DOCUMENTS, key, expires_in=1)

        # Czekanie zastępujemy podpisem, który wygasł, zanim powstał: MinIO
        # sprawdza znacznik czasu, więc efekt jest ten sam, a test nie śpi.
        expired = url.replace("X-Amz-Expires=1&", "X-Amz-Expires=0&")
        assert _fetch(expired) == 403


class TestPolicyIsReappliedOnRestart:
    """Polityka wraca przy każdym starcie, nie tylko przy zakładaniu bucketu."""

    def test_removed_policy_returns_after_bootstrap(self, manager: S3BucketManager):
        """Zdjęta polityka wraca po bootstrapie."""
        manager.client.delete_bucket_policy(Bucket=PRODUCTS.name)
        assert manager.bucket_policy(PRODUCTS.name) is None

        sync_buckets()

        assert manager.bucket_policy(PRODUCTS.name) is not None
