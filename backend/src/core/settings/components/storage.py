"""Konfiguracja magazynu plików.

Buckety są trzy i dzieli je polityka dostępu, nie rodzaj treści (ADR 0025):
`products` do odczytu publicznego, `originals` i `documents` prywatne.
Nazwy i polityki mieszkają w `core/storage/buckets.py` — tutaj jest tylko
połączenie z dostawcą.
"""

import os

from core.paths import BASE_DIR

STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_ROOT = BASE_DIR / "mediafiles"

# Pliki statyczne Django (panel, drf-spectacular) nie są treścią sklepu i nie
# mają swojego bucketa — ADR 0025 wymienia trzy, wszystkie na multimedia.
# Serwuje je warstwa przed aplikacją, tak samo w dev i w produkcji.
STATIC_URL = "/static/"
STATIC_ROOT = str(os.environ.get("STATIC_ROOT", STATIC_ROOT))

MEDIA_URL = "/media/"
MEDIA_ROOT = str(os.environ.get("MEDIA_ROOT", MEDIA_ROOT))

USE_AWS = bool(os.environ.get("USE_AWS", "False").lower() == "true")

AWS_ACCESS_KEY_ID = str(os.environ.get("AWS_ACCESS_KEY_ID", "minioadmin"))
AWS_SECRET_ACCESS_KEY = str(os.environ.get("AWS_SECRET_ACCESS_KEY", "minioadmin"))
AWS_S3_REGION_NAME = str(os.environ.get("AWS_S3_REGION_NAME", "us-east-1"))
AWS_S3_ENDPOINT_URL = str(os.environ.get("AWS_S3_ENDPOINT_URL", "http://minio:9000"))
AWS_S3_CUSTOM_DOMAIN = str(os.environ.get("AWS_S3_CUSTOM_DOMAIN", "localhost:9000"))
# Podpis w wersji czwartej. MinIO nie przyjmuje już adresów podpisanych
# starszą wersją, a boto3 domyślnie zaczyna właśnie od niej — bez tego
# adres do bucketa `documents` wyglądałby poprawnie i nie działał.
AWS_S3_SIGNATURE_VERSION = "s3v4"

if USE_AWS:
    AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=86400"}
    # Buckety nie mają list kontroli dostępu per obiekt — dostępem rządzi
    # polityka bucketa, nałożona przy starcie przez `sync_buckets`.
    AWS_DEFAULT_ACL = None
    AWS_S3_VERIFY = False
    AWS_S3_USE_SSL = False

    STORAGES = {
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
        # Domyślny magazyn jest prywatny świadomie: plik zapisany bez wskazania
        # miejsca ma wylądować tam, skąd nikt go nie pobierze bez podpisu,
        # a nie w buckecie otwartym na świat.
        "default": {"BACKEND": "core.storage.storages.OriginalStorage"},
    }
else:
    STORAGES = {
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    }
