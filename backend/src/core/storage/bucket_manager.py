import json
import os
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from django.conf import settings

from core.storage.buckets import (
    DEFAULT_URL_TTL_SECONDS,
    Bucket,
    public_read_policy,
)


class S3BucketManager:
    def __init__(self) -> None:
        self.config = self._build_config()
        self.client = self._build_client()

    def _build_config(self) -> Config:
        addressing_style = os.environ.get("AWS_S3_ADDRESSING_STYLE", "path")
        # botocore typuje `s3` jako wąski TypedDict domknięty na konkretne klucze,
        # więc zwykły dict — poprawny w czasie działania — nie przechodzi sprawdzenia.
        # Adnotacja `Any` mówi to wprost i przeżywa przeformatowanie pliku, czego
        # komentarz wyciszający na końcu linii nie robi.
        s3_options: Any = {"addressing_style": addressing_style}
        return Config(
            signature_version="s3v4",
            s3=s3_options,
        )

    def _build_client(self):
        aws_access_key_id = getattr(
            settings,
            "AWS_ACCESS_KEY_ID",
            os.environ.get("AWS_ACCESS_KEY_ID", "minioadmin"),
        )
        aws_secret_access_key = getattr(
            settings,
            "AWS_SECRET_ACCESS_KEY",
            os.environ.get("AWS_SECRET_ACCESS_KEY", "minioadmin"),
        )
        region_name = getattr(
            settings,
            "AWS_S3_REGION_NAME",
            os.environ.get("AWS_S3_REGION_NAME", "us-east-1"),
        )
        endpoint_url = getattr(
            settings,
            "AWS_S3_ENDPOINT_URL",
            os.environ.get("AWS_S3_ENDPOINT_URL", "http://minio:9000"),
        )
        use_ssl = getattr(
            settings,
            "AWS_S3_USE_SSL",
            os.environ.get("AWS_S3_USE_SSL", "False").lower() == "true",
        )

        # Opcjonalne: pomijamy endpoint_url jeśli łączymy się oryginalnie z AWS bez nadpisania
        use_aws = getattr(
            settings, "USE_AWS", os.environ.get("USE_AWS", "False").lower() == "true"
        )
        client_kwargs = {
            "aws_access_key_id": aws_access_key_id,
            "aws_secret_access_key": aws_secret_access_key,
            "region_name": region_name,
            "use_ssl": use_ssl,
            "config": self.config,
        }

        # Jeśli nie używamy czystego AWS'a lub wyraźnie jest podany inny endpoint, dodajemy endpoint_url
        if endpoint_url and not (use_aws and "amazonaws.com" not in endpoint_url):
            client_kwargs["endpoint_url"] = endpoint_url

        # Upewniamy się, że w trybie AWS pominie lokalny endpoint
        if use_aws and ("localhost" in endpoint_url or "minio" in endpoint_url):
            client_kwargs.pop("endpoint_url", None)

        return boto3.client("s3", **client_kwargs)

    def bucket_exists(self, bucket_name: str) -> bool:
        """
        Sprawdź, czy bucket istnieje w dostawcy magazynu S3.

        Args:
            bucket_name (str): Nazwa bucketu do sprawdzenia.

        Returns:
            bool: True jeśli bucket istnieje, False w przeciwnym razie.
        """
        try:
            self.client.head_bucket(Bucket=bucket_name)
            return True
        except ClientError:
            return False

    def create_bucket(self, bucket_name: str) -> None:
        """
        Utwórz bucket w dostawcy magazynu S3.

        Args:
            bucket_name (str): Nazwa bucketu do utworzenia.
        """
        kwargs: dict = {"Bucket": bucket_name}

        region = getattr(
            settings,
            "AWS_S3_REGION_NAME",
            os.environ.get("AWS_S3_REGION_NAME", "us-east-1"),
        )
        use_aws = getattr(
            settings, "USE_AWS", os.environ.get("USE_AWS", "False").lower() == "true"
        )

        if region != "us-east-1" and use_aws:
            kwargs["CreateBucketConfiguration"] = {"LocationConstraint": region}

        self.client.create_bucket(**kwargs)

    def ensure_bucket(self, bucket_name: str) -> None:
        """
        Upewnij się, że bucket istnieje w dostawcy magazynu S3. Jeśli nie istnieje, utwórz go.

        Args:
            bucket_name (str): Nazwa bucketu do upewnienia się.
        """
        if not self.bucket_exists(bucket_name):
            self.create_bucket(bucket_name)

    def apply_access(self, bucket: Bucket) -> None:
        """Nakłada na bucket politykę wynikającą z jego przeznaczenia (ADR 0025).

        Polityka jest nakładana przy każdym uruchomieniu, a nie tylko przy
        tworzeniu bucketu: inaczej bucket założony wcześniej ręcznie zostałby
        z polityką, której nikt nie pilnuje.
        """
        if bucket.is_public:
            self.client.put_bucket_policy(
                Bucket=bucket.name,
                Policy=json.dumps(public_read_policy(bucket.name)),
            )
            return
        # Prywatny znaczy „bez polityki wpuszczającej kogokolwiek". Kasujemy
        # tę, która ewentualnie została — brak polityki to odmowa domyślna.
        try:
            self.client.delete_bucket_policy(Bucket=bucket.name)
        except ClientError:
            pass

    def ensure(self, bucket: Bucket) -> bool:
        """Zakłada bucket, jeśli trzeba, i nakłada jego politykę.

        Returns:
            bool: True, jeśli bucket powstał w tym wywołaniu.
        """
        created = not self.bucket_exists(bucket.name)
        if created:
            self.create_bucket(bucket.name)
        self.apply_access(bucket)
        return created

    def bucket_policy(self, bucket_name: str) -> dict | None:
        """Polityka bucketu albo `None`, gdy żadnej nie ma."""
        try:
            response = self.client.get_bucket_policy(Bucket=bucket_name)
        except ClientError:
            return None
        return json.loads(response["Policy"])

    def presigned_url(
        self,
        bucket: Bucket,
        key: str,
        expires_in: int = DEFAULT_URL_TTL_SECONDS,
    ) -> str:
        """Adres do prywatnego obiektu, ważny przez zadany czas.

        Jedyna droga do bucketa `documents`: dokument sprzedaży i certyfikat
        kamienia są dostępne dla tego, komu sklep poda odnośnik, i tylko na
        czas jego ważności.
        """
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket.name, "Key": key},
            ExpiresIn=expires_in,
        )

    def delete_bucket(self, bucket_name: str) -> None:
        """Usuń bucket z dostawcy magazynu S3.

        Args:
            bucket_name (str): Nazwa bucketu do usunięcia.
        """
        self.client.delete_bucket(Bucket=bucket_name)

    def list_buckets(self) -> list:
        """Zwróć listę wszystkich bucketów w dostawcy magazynu S3.

        Returns:
            list: Lista nazw bucketów.
        """
        response = self.client.list_buckets()
        return [bucket["Name"] for bucket in response.get("Buckets", [])]
