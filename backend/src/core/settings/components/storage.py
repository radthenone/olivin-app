"""Konfiguracja magazynu plików.

Buckety są trzy i dzieli je polityka dostępu, nie rodzaj treści (ADR 0025):
`products` do odczytu publicznego, `originals` i `documents` prywatne.
Nazwy i polityki mieszkają w `core/storage/buckets.py` — tutaj jest tylko
połączenie z dostawcą.

Konfiguracja jest neutralna wobec dostawcy S3: ten sam kod działa z każdym
magazynem mówiącym S3. Flaga `USE_S3` mówi tylko „S3 albo dysk". Pusty
`AWS_S3_ENDPOINT_URL` oznacza właściwy AWS, nie brak konfiguracji.
"""

import os

from django.core.exceptions import ImproperlyConfigured

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

USE_S3 = os.environ.get("USE_S3", "False").lower() == "true"

AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID") or None
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY") or None
AWS_S3_REGION_NAME = os.environ.get("AWS_S3_REGION_NAME", "us-east-1")
# Pusty adres oznacza właściwy AWS — wtedy boto3 nie dostaje `endpoint_url`.
AWS_S3_ENDPOINT_URL = os.environ.get("AWS_S3_ENDPOINT_URL", "")
AWS_S3_ADDRESSING_STYLE = os.environ.get("AWS_S3_ADDRESSING_STYLE", "path")
AWS_S3_URL_PROTOCOL = os.environ.get("AWS_S3_URL_PROTOCOL", "http:")
AWS_S3_CUSTOM_DOMAIN = os.environ.get("AWS_S3_CUSTOM_DOMAIN", "")
# Bazowy adres publicznych plików; może mieć prefiks ścieżki.
S3_PUBLIC_BASE_URL = os.environ.get("S3_PUBLIC_BASE_URL", "")

if AWS_S3_ADDRESSING_STYLE not in ("path", "virtual"):
    raise ImproperlyConfigured(
        "AWS_S3_ADDRESSING_STYLE ma być 'path' albo 'virtual', "
        f"a jest {AWS_S3_ADDRESSING_STYLE!r}."
    )

if AWS_S3_URL_PROTOCOL not in ("http:", "https:"):
    raise ImproperlyConfigured(
        "AWS_S3_URL_PROTOCOL ma być 'http:' albo 'https:', "
        f"a jest {AWS_S3_URL_PROTOCOL!r}."
    )

if USE_S3 and (not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY):
    raise ImproperlyConfigured(
        "USE_S3=true wymaga AWS_ACCESS_KEY_ID i AWS_SECRET_ACCESS_KEY. "
        "Bez credentiali magazyn nie startuje — zamiast otwartego magazynu."
    )

# Podpis w wersji czwartej. Dostawcy S3 nie przyjmują już adresów podpisanych
# starszą wersją, a boto3 domyślnie zaczyna właśnie od niej — bez tego
# adres do bucketa `documents` wyglądałby poprawnie i nie działał.
AWS_S3_SIGNATURE_VERSION = "s3v4"

if USE_S3:
    AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=86400"}
    # Buckety nie mają list kontroli dostępu per obiekt — dostępem rządzi
    # polityka bucketa, nałożona przy starcie przez `sync_buckets`.
    AWS_DEFAULT_ACL = None
    AWS_S3_USE_SSL = AWS_S3_URL_PROTOCOL == "https:"

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
