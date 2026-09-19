"""Klasy magazynu — po jednej na bucket z ADR 0025.

Model trzyma wyłącznie klucz obiektu: bez hosta i bez nazwy bucketa. Adres
składa warstwa serializacji, bo host zmienia się razem ze środowiskiem
(MinIO w dev, S3 w produkcji), a klucz zapisany razem z hostem trzeba by
migrować przy każdej takiej zmianie.
"""

import os

from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage

from core.storage.buckets import DOCUMENTS, ORIGINALS, PRODUCTS, Bucket


class BucketStorage(S3Boto3Storage):
    """Magazyn związany z jednym bucketem i jego polityką."""

    bucket: Bucket

    @classmethod
    def _get_endpoint_url(cls) -> str | None:
        """Adres dostawcy. `None` oznacza właściwy AWS, nie brak konfiguracji."""
        configured = getattr(settings, "AWS_S3_ENDPOINT_URL", None)
        if configured:
            return configured
        return os.environ.get("AWS_S3_ENDPOINT_URL") or None

    @classmethod
    def _get_custom_domain(cls) -> str:
        return getattr(
            settings,
            "AWS_S3_CUSTOM_DOMAIN",
            os.environ.get("AWS_S3_CUSTOM_DOMAIN", "localhost:9000"),
        ).rstrip("/")

    def __init__(self, **kwargs):
        self.bucket_name = self.bucket.name
        self.endpoint_url = self._get_endpoint_url()
        use_aws = getattr(
            settings,
            "USE_AWS",
            os.environ.get("USE_AWS", "False").lower() == "true",
        )
        if self.bucket.is_public:
            domain = self._get_custom_domain()
            # Na S3 host zawiera już bucket; MinIO adresuje ścieżką, więc
            # nazwa bucketa musi wejść do adresu. Bez ukośnika na końcu —
            # django-storages dokłada go sam i inaczej wychodzi `//`.
            self.custom_domain = (
                domain if use_aws else f"{domain}/{self.bucket.name.strip('/')}"
            )
            self.url_protocol = "https:" if use_aws else "http:"
        else:
            # Prywatny bucket nie może mieć własnej domeny: django-storages
            # zwraca wtedy gotowy adres i **pomija podpisywanie**, czyli
            # `documents` przestałoby być prywatne w jedyny sposób, w jaki
            # o tym wiemy — przez adres, który nie działa bez podpisu.
            self.custom_domain = None
        super().__init__(**kwargs)


class ProductStorage(BucketStorage):
    """Zdjęcia katalogu — odczyt publiczny, adres bez podpisu."""

    bucket = PRODUCTS
    location = ""
    default_acl = None
    file_overwrite = True
    querystring_auth = False


class OriginalStorage(BucketStorage):
    """Oryginały zdjęć — prywatne, czytane wyłącznie przez zadania w tle."""

    bucket = ORIGINALS
    location = ""
    default_acl = None
    file_overwrite = False
    querystring_auth = True


class DocumentStorage(BucketStorage):
    """Dokumenty sprzedaży i certyfikaty — prywatne, adres podpisany na czas."""

    bucket = DOCUMENTS
    location = ""
    default_acl = None
    file_overwrite = False
    querystring_auth = True


_BY_BUCKET: dict[str, type[BucketStorage]] = {
    PRODUCTS.name: ProductStorage,
    ORIGINALS.name: OriginalStorage,
    DOCUMENTS.name: DocumentStorage,
}


def storage_for(bucket: Bucket) -> BucketStorage:
    """Magazyn obsługujący dany bucket.

    Pozwala warstwie serializacji poprosić o adres, podając bucket z ADR 0025,
    bez wiedzy o tym, która klasa go obsługuje.
    """
    try:
        return _BY_BUCKET[bucket.name]()
    except KeyError:
        raise ValueError(f"Nie ma magazynu dla bucketa {bucket.name}") from None
