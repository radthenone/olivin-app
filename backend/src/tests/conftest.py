from __future__ import annotations

import os
from unittest.mock import patch

import fakeredis
import pytest
from moto import mock_aws
from rest_framework.test import APIClient

from apps.accounts.models import CustomUser


@pytest.fixture(autouse=True)
def mock_s3_storage():
    """Globalsize mock AWS/S3 dla środowiska testowego, zapobiega wgrywaniu prawdziwych plików do MinIO."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
    with mock_aws():
        # Czasami trzeba stworzyć na szybko mockowy bucket do użycia przez django-storages
        import boto3

        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket="test-bucket")
        yield


@pytest.fixture(autouse=True)
def mock_redis_connection():
    """Zastępuje wszystkie instancje Redis na FakeRedis w ramach testów, żeby przyspieszyć cache/broker."""
    server = fakeredis.FakeServer()
    mock_redis_instance = fakeredis.FakeStrictRedis(server=server)

    with (
        patch("redis.Redis", return_value=mock_redis_instance),
        patch("redis.StrictRedis", return_value=mock_redis_instance),
    ):
        yield mock_redis_instance


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def user(db) -> CustomUser:
    return CustomUser.objects.create_user(
        email="user@test.com",
        password="testpass123!",
        first_name="Jan",
        last_name="Kowalski",
    )


@pytest.fixture
def admin_user(db) -> CustomUser:
    return CustomUser.objects.create_superuser(
        email="admin@test.com",
        password="adminpass123!",
    )


@pytest.fixture
def authenticated_client(api_client: APIClient, user: CustomUser) -> APIClient:
    api_client.force_authenticate(user=user)
    return api_client
