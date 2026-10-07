"""Buckety podzielone polityką dostępu (ADR 0025)."""

from __future__ import annotations

import pytest

from core.paths import CORE_DIR
from core.storage.buckets import (
    ALL_BUCKETS,
    DOCUMENTS,
    ORIGINALS,
    PRODUCTS,
    BucketAccess,
    public_read_policy,
)
from core.storage.storages import (
    DocumentStorage,
    OriginalStorage,
    ProductStorage,
    storage_for,
)
from core.storage.urls import object_url
from core.storage.utils import sync_buckets

OLD_BUCKET_NAMES = ("static", "media", "profiles", "private-media")


class TestBucketDefinitions:
    """Trzy buckety, podział po polityce dostępu, nie po rodzaju treści."""

    def test_there_are_exactly_three(self):
        """Są dokładnie trzy buckety."""
        assert len(ALL_BUCKETS) == 3

    def test_products_is_public(self):
        """Bucket `products` jest publiczny."""
        assert PRODUCTS.access is BucketAccess.PUBLIC_READ
        assert PRODUCTS.is_public

    @pytest.mark.parametrize("bucket", [ORIGINALS, DOCUMENTS])
    def test_others_are_private(self, bucket):
        """Pozostałe buckety są prywatne."""
        assert bucket.access is BucketAccess.PRIVATE
        assert not bucket.is_public

    def test_names_are_distinct(self):
        """Nazwy bucketów są rozłączne."""
        names = [bucket.name for bucket in ALL_BUCKETS]
        assert len(set(names)) == 3


class TestPublicPolicy:
    """Publiczny odczyt obiektów, ale nie spis zawartości."""

    def test_allows_anyone_to_read_object(self):
        """Polityka wpuszcza każdego do odczytu obiektu."""
        policy = public_read_policy("products")
        statement = policy["Statement"][0]

        assert statement["Effect"] == "Allow"
        assert statement["Principal"] == {"AWS": ["*"]}
        assert statement["Action"] == ["s3:GetObject"]
        assert statement["Resource"] == ["arn:aws:s3:::products/*"]

    def test_does_not_allow_listing(self):
        """Polityka nie wpuszcza do listowania."""
        policy = public_read_policy("products")
        actions = {
            action
            for statement in policy["Statement"]
            for action in statement["Action"]
        }

        assert "s3:ListBucket" not in actions


class TestOldNamesAreGone:
    """Dotychczasowe nazwy znikają z kodu — nie zostają jako martwe klasy."""

    def test_not_among_buckets(self):
        """Starych nazw nie ma wśród bucketów."""
        names = {bucket.name for bucket in ALL_BUCKETS}

        assert names.isdisjoint(OLD_BUCKET_NAMES)

    def test_not_in_storage_module(self):
        """Starych nazw nie ma w module magazynu."""
        source = (CORE_DIR / "storage" / "storages.py").read_text(encoding="utf-8")

        for legacy in ("ProfileStorage", "PublicMediaStorage", "PrivateMediaStorage"):
            assert legacy not in source

    def test_not_in_storage_settings(self):
        """Starych nazw nie ma w ustawieniach magazynu."""
        source = (CORE_DIR / "settings" / "components" / "storage.py").read_text(
            encoding="utf-8"
        )

        assert "private-media" not in source
        assert "AWS_STORAGE_BUCKET_NAME" not in source


class TestStorageRegistry:
    """Każdy bucket ma swoją klasę magazynu — i odwrotnie."""

    @pytest.mark.parametrize(
        ("bucket", "expected"),
        [
            (PRODUCTS, ProductStorage),
            (ORIGINALS, OriginalStorage),
            (DOCUMENTS, DocumentStorage),
        ],
    )
    def test_bucket_points_to_its_storage(self, bucket, expected):
        """Bucket wskazuje swoją klasę magazynu."""
        assert isinstance(storage_for(bucket), expected)

    def test_storage_knows_its_bucket(self):
        """Magazyn zna swój bucket."""
        assert ProductStorage().bucket_name == PRODUCTS.name
        assert ProductStorage.bucket_spec is PRODUCTS

    def test_catalog_images_are_not_signed(self):
        """Zdjęcia katalogu nie podpisują adresu."""
        assert ProductStorage.querystring_auth is False

    @pytest.mark.parametrize("storage", [OriginalStorage, DocumentStorage])
    def test_private_storages_sign_url(self, storage):
        """Prywatne magazyny podpisują adres."""
        assert storage.querystring_auth is True

    def test_unknown_bucket_raises_instead_of_none(self):
        """Nieznany bucket jest błędem, a nie cichym `None`."""
        from core.storage.buckets import Bucket

        with pytest.raises(ValueError):
            storage_for(Bucket("nieznany", BucketAccess.PRIVATE, "—"))


@pytest.mark.django_db
class TestStorageReadsAndWrites:
    """Przez magazyn da się zapisać i odczytać plik.

    Wygląda na oczywiste, a nie jest: `S3Boto3Storage` ma własny atrybut
    `bucket` — zasób boto3, przez który idzie całe wejście-wyjście. Nazwanie
    tak samo naszego opisu bucketa przesłania go i wywraca każdy zapis,
    nie ruszając przy tym żadnego testu na kształt polityki.
    """

    @pytest.mark.parametrize(
        "storage_class", [ProductStorage, OriginalStorage, DocumentStorage]
    )
    def test_write_and_read_return_same_content(self, storage_class):
        """Zapis i odczyt zwracają tę samą treść."""
        from django.core.files.base import ContentFile

        storage = storage_class()
        key = storage.save("probe/olivin.txt", ContentFile(b"olivin"))

        with storage.open(key, "rb") as handle:
            assert handle.read() == b"olivin"

    @pytest.mark.parametrize(
        "storage_class", [ProductStorage, OriginalStorage, DocumentStorage]
    )
    def test_storage_sees_boto3_bucket_resource(self, storage_class):
        """Magazyn widzi zasób bucketa z boto3."""
        assert hasattr(storage_class().bucket, "Object")


@pytest.mark.django_db
class TestObjectUrl:
    """Model trzyma sam klucz; adres składa warstwa serializacji."""

    def test_public_bucket_gives_unsigned_url(self):
        """Publiczny bucket daje adres bez podpisu."""
        url = object_url(PRODUCTS, "abc/large.webp")

        assert "abc/large.webp" in url
        assert "X-Amz-Signature" not in url

    def test_private_bucket_gives_signed_url(self):
        """Prywatny bucket daje adres podpisany."""
        url = object_url(DOCUMENTS, "certificates/abc.pdf")

        assert "certificates/abc.pdf" in url
        assert "X-Amz-Signature" in url

    def test_signed_url_has_expiry(self):
        """Adres podpisany ma czas ważności."""
        url = object_url(DOCUMENTS, "certificates/abc.pdf", expires_in=60)

        assert "X-Amz-Expires=60" in url

    def test_key_does_not_contain_host(self):
        """Klucz jest tym, co trzyma model — bez hosta i bez bucketa."""
        key = "certificates/abc.pdf"
        url = object_url(DOCUMENTS, key)

        assert url.count(key) == 1


@pytest.mark.django_db
class TestSyncBuckets:
    """Bootstrap zakłada buckety i nakłada polityki — i niczego nie kasuje."""

    def test_creates_all_three(self):
        """Bootstrap zakłada wszystkie trzy buckety."""
        from core.storage.bucket_manager import S3BucketManager

        manager = S3BucketManager()
        for bucket in ALL_BUCKETS:
            if manager.bucket_exists(bucket.name):
                manager.client.delete_bucket(Bucket=bucket.name)

        result = sync_buckets()

        assert result.success
        assert sorted(result.created) == sorted(bucket.name for bucket in ALL_BUCKETS)

    def test_second_run_creates_nothing(self):
        """Drugi przebieg niczego nie zakłada."""
        sync_buckets()

        result = sync_buckets()

        assert result.success
        assert result.created == []
        assert sorted(result.updated) == sorted(bucket.name for bucket in ALL_BUCKETS)

    def test_does_not_delete_unlisted_bucket(self):
        """Bootstrap przy starcie kontenera nie jest miejscem na kasowanie
        magazynu — wcześniejsza wersja usuwała wszystko spoza listy."""
        from core.storage.bucket_manager import S3BucketManager

        manager = S3BucketManager()
        manager.ensure_bucket("obcy-bucket")

        sync_buckets()

        assert manager.bucket_exists("obcy-bucket")
