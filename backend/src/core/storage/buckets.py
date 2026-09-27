"""Trzy buckety podzielone polityką dostępu (ADR 0025).

Podział idzie po tym, kto ma prawo czytać, a nie po tym, co leży w środku.
Jeden bucket z prefiksami odrzucono świadomie: pomyłka w jednej regule
wystawiłaby dokumenty klientów do internetu.

Nazwy są jednym źródłem prawdy dla bootstrapu MinIO, klas magazynu i testów
polityk — rozjazd między nimi kończy się plikiem zapisanym tam, gdzie nikt
go nie szuka.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import StrEnum


class BucketAccess(StrEnum):
    PUBLIC_READ = "public-read"
    PRIVATE = "private"


@dataclass(frozen=True, slots=True)
class Bucket:
    name: str
    access: BucketAccess
    purpose: str

    @property
    def is_public(self) -> bool:
        return self.access is BucketAccess.PUBLIC_READ


PRODUCTS = Bucket(
    name=os.environ.get("S3_BUCKET_PRODUCTS", "products"),
    access=BucketAccess.PUBLIC_READ,
    purpose="Zdjęcia katalogu w rozmiarach gotowych do pokazania",
)
ORIGINALS = Bucket(
    name=os.environ.get("S3_BUCKET_ORIGINALS", "originals"),
    access=BucketAccess.PRIVATE,
    purpose="Oryginały zdjęć zachowane na wypadek zmiany kadru",
)
DOCUMENTS = Bucket(
    name=os.environ.get("S3_BUCKET_DOCUMENTS", "documents"),
    access=BucketAccess.PRIVATE,
    purpose="Dokumenty sprzedaży i certyfikaty kamieni — adres podpisany na czas",
)

ALL_BUCKETS: tuple[Bucket, ...] = (PRODUCTS, ORIGINALS, DOCUMENTS)

# Domyślny czas ważności adresu podpisanego. Godzina wystarcza na pobranie
# dokumentu, a jest krótsza niż czas życia odnośnika przesłanego dalej mailem.
DEFAULT_URL_TTL_SECONDS = int(os.environ.get("S3_SIGNED_URL_TTL", 3600))


def public_read_policy(bucket_name: str) -> dict:
    """Polityka wpuszczająca każdego do odczytu obiektów, ale nie do listowania.

    Listowanie zostaje zamknięte celowo: publiczny odczyt ma dawać dostęp do
    znanego adresu zdjęcia, a nie spis całej zawartości katalogu.
    """
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "PublicReadObjects",
                "Effect": "Allow",
                "Principal": {"AWS": ["*"]},
                "Action": ["s3:GetObject"],
                "Resource": [f"arn:aws:s3:::{bucket_name}/*"],
            }
        ],
    }
