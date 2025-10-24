"""
Storage configuration for Olivin project.

This module handles static and media file storage configuration.
Supports both local file storage and S3/MinIO storage.
"""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_ROOT = BASE_DIR / "mediafiles"

# Static files configuration
STATIC_URL = "/static/"
STATIC_ROOT = str(os.environ.get("STATIC_ROOT", STATIC_ROOT))

# Media files configuration
MEDIA_URL = "/media/"
MEDIA_ROOT = str(os.environ.get("MEDIA_ROOT", MEDIA_ROOT))

# Storage backend configuration
USE_AWS = bool(os.environ.get("USE_AWS", "False").lower() == "true")

if USE_AWS:
    # S3/MinIO storage configuration
    STATICFILES_STORAGE = "core.storages.StaticStorage"
    DEFAULT_FILE_STORAGE = "core.storages.PublicMediaStorage"
    PRIVATE_FILE_STORAGE = "core.storages.PrivateMediaStorage"

    STORAGES = {
        "staticfiles": {"BACKEND": STATICFILES_STORAGE},
        "default": {"BACKEND": DEFAULT_FILE_STORAGE},
    }

    # AWS/S3 settings
    AWS_ACCESS_KEY_ID = str(os.environ.get("AWS_ACCESS_KEY_ID", "minioadmin"))
    AWS_SECRET_ACCESS_KEY = str(os.environ.get("AWS_SECRET_ACCESS_KEY", "minioadmin"))
    AWS_S3_REGION_NAME = str(os.environ.get("AWS_S3_REGION_NAME", "us-east-1"))
    AWS_S3_ENDPOINT_URL = str(os.environ.get("AWS_S3_ENDPOINT_URL", "http://minio:9000"))
    AWS_S3_CUSTOM_DOMAIN = str(os.environ.get("AWS_S3_CUSTOM_DOMAIN", "localhost:9000"))
    AWS_STORAGE_BUCKET_NAME = str(os.environ.get("AWS_STORAGE_BUCKET_NAME", "static"))

    # S3 specific settings
    AWS_S3_OBJECT_PARAMETERS = {
        "CacheControl": "max-age=86400",
    }
    AWS_DEFAULT_ACL = None
    AWS_S3_VERIFY = False
    AWS_S3_USE_SSL = False
else:
    # Local file storage (default for development)
    STORAGES = {
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    }

    # MinIO settings for bucket initialization only
    AWS_ACCESS_KEY_ID = str(os.environ.get("AWS_ACCESS_KEY_ID", "minioadmin"))
    AWS_SECRET_ACCESS_KEY = str(os.environ.get("AWS_SECRET_ACCESS_KEY", "minioadmin"))
    AWS_S3_ENDPOINT_URL = str(os.environ.get("AWS_S3_ENDPOINT_URL", "http://minio:9000"))
    AWS_STORAGE_BUCKET_NAME = str(os.environ.get("AWS_STORAGE_BUCKET_NAME", "static"))