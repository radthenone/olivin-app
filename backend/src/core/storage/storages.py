import os

from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class DefaultStorage(S3Boto3Storage):
    bucket_name = ""

    @classmethod
    def _get_endpoint_url(cls) -> str:
        return getattr(
            settings,
            "AWS_S3_ENDPOINT_URL",
            os.environ.get("AWS_S3_ENDPOINT_URL", "http://minio:9000"),
        )

    @classmethod
    def _get_custom_domain(cls) -> str:
        return getattr(
            settings,
            "AWS_S3_CUSTOM_DOMAIN",
            os.environ.get("AWS_S3_CUSTOM_DOMAIN", "localhost:9000"),
        ).rstrip("/")

    def __init__(self, **kwargs):
        self.endpoint_url = self._get_endpoint_url()
        domain = self._get_custom_domain()
        use_aws = getattr(
            settings,
            "USE_AWS",
            os.environ.get("USE_AWS", "False").lower() == "true",
        )
        if use_aws:
            self.custom_domain = f"{domain}/"
        else:
            bucket = self.bucket_name.strip("/")
            self.custom_domain = f"{domain}/{bucket}/"
        super().__init__(**kwargs)


class PublicStorage(DefaultStorage):
    default_acl = "public-read"
    file_overwrite = True
    secure_urls = False
    use_ssl = False
    url_protocol = "http:"

    @property
    def querystring_auth(self):
        return False


class PrivateStorage(DefaultStorage):
    default_acl = "private"
    file_overwrite = False
    secure_urls = False
    use_ssl = False
    url_protocol = "http:"

    @property
    def querystring_auth(self):
        return False


class StaticStorage(PublicStorage):
    location = ""

    def __init__(self, **kwargs):
        self.bucket_name = getattr(
            settings,
            "AWS_STORAGE_BUCKET_NAME",
            os.environ.get("AWS_STORAGE_BUCKET_NAME", "static"),
        )
        super().__init__(**kwargs)


class ProfileStorage(PublicStorage):
    bucket_name = "profiles"
    location = ""


class ProductStorage(PublicStorage):
    bucket_name = "products"
    location = ""


class PublicMediaStorage(PublicStorage):
    """
    Storage dla publicznych plików multimedialnych.
    Używane jako domyślne storage dla uploadowanych plików.
    """

    bucket_name = "media"
    location = ""


class PrivateMediaStorage(PrivateStorage):
    """
    Storage dla prywatnych plików multimedialnych.
    Używane dla plików wymagających autoryzacji.
    """

    bucket_name = "private-media"
    location = ""
