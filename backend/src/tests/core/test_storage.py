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

    def test_sa_dokladnie_trzy(self):
        assert len(ALL_BUCKETS) == 3

    def test_products_jest_publiczny(self):
        assert PRODUCTS.access is BucketAccess.PUBLIC_READ
        assert PRODUCTS.is_public

    @pytest.mark.parametrize("bucket", [ORIGINALS, DOCUMENTS])
    def test_pozostale_sa_prywatne(self, bucket):
        assert bucket.access is BucketAccess.PRIVATE
        assert not bucket.is_public

    def test_nazwy_sa_rozlaczne(self):
        names = [bucket.name for bucket in ALL_BUCKETS]
        assert len(set(names)) == 3


class TestPublicPolicy:
    """Publiczny odczyt obiektów, ale nie spis zawartości."""

    def test_wpuszcza_kazdego_do_odczytu_obiektu(self):
        policy = public_read_policy("products")
        statement = policy["Statement"][0]

        assert statement["Effect"] == "Allow"
        assert statement["Principal"] == {"AWS": ["*"]}
        assert statement["Action"] == ["s3:GetObject"]
        assert statement["Resource"] == ["arn:aws:s3:::products/*"]

    def test_nie_wpuszcza_do_listowania(self):
        policy = public_read_policy("products")
        actions = {
            action
            for statement in policy["Statement"]
            for action in statement["Action"]
        }

        assert "s3:ListBucket" not in actions


class TestOldNamesAreGone:
    """Dotychczasowe nazwy znikają z kodu — nie zostają jako martwe klasy."""

    def test_nie_ma_ich_wsrod_bucketow(self):
        names = {bucket.name for bucket in ALL_BUCKETS}

        assert names.isdisjoint(OLD_BUCKET_NAMES)

    def test_nie_ma_ich_w_module_magazynu(self):
        source = (CORE_DIR / "storage" / "storages.py").read_text(encoding="utf-8")

        for legacy in ("ProfileStorage", "PublicMediaStorage", "PrivateMediaStorage"):
            assert legacy not in source

    def test_nie_ma_ich_w_ustawieniach_magazynu(self):
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
    def test_bucket_wskazuje_swoj_magazyn(self, bucket, expected):
        assert isinstance(storage_for(bucket), expected)

    def test_magazyn_zna_swoj_bucket(self):
        assert ProductStorage().bucket_name == PRODUCTS.name
        assert ProductStorage.bucket_spec is PRODUCTS

    def test_zdjecia_katalogu_nie_podpisuja_adresu(self):
        assert ProductStorage.querystring_auth is False

    @pytest.mark.parametrize("storage", [OriginalStorage, DocumentStorage])
    def test_prywatne_podpisuja_adres(self, storage):
        assert storage.querystring_auth is True

    def test_nieznany_bucket_jest_bledem_a_nie_cichym_none(self):
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
    def test_zapis_i_odczyt_wracaja_ta_sama_trescia(self, storage_class):
        from django.core.files.base import ContentFile

        storage = storage_class()
        key = storage.save("probe/olivin.txt", ContentFile(b"olivin"))

        with storage.open(key, "rb") as handle:
            assert handle.read() == b"olivin"

    @pytest.mark.parametrize(
        "storage_class", [ProductStorage, OriginalStorage, DocumentStorage]
    )
    def test_magazyn_widzi_zasob_bucketa_z_boto3(self, storage_class):
        assert hasattr(storage_class().bucket, "Object")


@pytest.mark.django_db
class TestObjectUrl:
    """Model trzyma sam klucz; adres składa warstwa serializacji."""

    def test_publiczny_bucket_daje_adres_bez_podpisu(self):
        url = object_url(PRODUCTS, "abc/large.webp")

        assert "abc/large.webp" in url
        assert "X-Amz-Signature" not in url

    def test_prywatny_bucket_daje_adres_podpisany(self):
        url = object_url(DOCUMENTS, "certificates/abc.pdf")

        assert "certificates/abc.pdf" in url
        assert "X-Amz-Signature" in url

    def test_adres_podpisany_ma_czas_waznosci(self):
        url = object_url(DOCUMENTS, "certificates/abc.pdf", expires_in=60)

        assert "X-Amz-Expires=60" in url

    def test_adres_nie_zawiera_hosta_w_kluczu(self):
        """Klucz jest tym, co trzyma model — bez hosta i bez bucketa."""
        key = "certificates/abc.pdf"
        url = object_url(DOCUMENTS, key)

        assert url.count(key) == 1


@pytest.mark.django_db
class TestSyncBuckets:
    """Bootstrap zakłada buckety i nakłada polityki — i niczego nie kasuje."""

    def test_zaklada_wszystkie_trzy(self):
        from core.storage.bucket_manager import S3BucketManager

        manager = S3BucketManager()
        for bucket in ALL_BUCKETS:
            if manager.bucket_exists(bucket.name):
                manager.client.delete_bucket(Bucket=bucket.name)

        result = sync_buckets()

        assert result.success
        assert sorted(result.created) == sorted(bucket.name for bucket in ALL_BUCKETS)

    def test_drugi_przebieg_niczego_nie_zaklada(self):
        sync_buckets()

        result = sync_buckets()

        assert result.success
        assert result.created == []
        assert sorted(result.updated) == sorted(bucket.name for bucket in ALL_BUCKETS)

    def test_nie_kasuje_bucketa_spoza_listy(self):
        """Bootstrap przy starcie kontenera nie jest miejscem na kasowanie
        magazynu — wcześniejsza wersja usuwała wszystko spoza listy."""
        from core.storage.bucket_manager import S3BucketManager

        manager = S3BucketManager()
        manager.ensure_bucket("obcy-bucket")

        sync_buckets()

        assert manager.bucket_exists("obcy-bucket")
