from datetime import timedelta

from django.conf import settings
from PIL import Image
from storages.backends.s3boto3 import S3Boto3Storage


class DefaultStorage(S3Boto3Storage):
    endpoint_url = settings.AWS_S3_ENDPOINT_URL
    bucket_name = ""
    custom_domain = settings.AWS_S3_CUSTOM_DOMAIN.rstrip("/")

    @property
    def custom_domain_with_bucket(self):
        domain = self.custom_domain
        bucket = self.bucket_name.strip("/")
        return f"{domain}/{bucket}/"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if settings.USE_AWS:
            self.custom_domain = f"{self.custom_domain}/"
        else:
            self.custom_domain = self.custom_domain_with_bucket


class PublicStorage(DefaultStorage):
    default_acl = "public-read"
    file_overwrite = True
    secure_urls = False
    use_ssl = False
    url_protocol = "http:"

    @property
    def querystring_auth(self):
        return False


class PublicStorageExpire(DefaultStorage):
    default_acl = "public-read"
    file_overwrite = True
    secure_urls = False
    use_ssl = False
    url_protocol = "http:"
    querystring_expire = timedelta(minutes=10).total_seconds()

    @property
    def querystring_auth(self):
        return True


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
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    location = ""


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