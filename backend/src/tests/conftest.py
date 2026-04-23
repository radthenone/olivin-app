from __future__ import annotations

import os
from unittest.mock import patch

import fakeredis
import pytest
from moto import mock_aws
from rest_framework.test import APIClient

from apps.accounts.models import CustomUser


@pytest.fixture(autouse=True)
def mock_s3_storage(request):
    """Globalny mock AWS/S3 dla testów unit/in-memory.

    Dla testów integracyjnych (marker `integration`) mock jest wyłączony,
    bo testy mają korzystać z prawdziwego MinIO/S3.
    """

    if request.node.get_closest_marker("integration") is not None:
        yield
        return

    keys_to_restore = [
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_SECURITY_TOKEN",
        "AWS_SESSION_TOKEN",
        "AWS_DEFAULT_REGION",
    ]
    previous_env = {key: os.environ.get(key) for key in keys_to_restore}

    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

    try:
        with mock_aws():
            # Czasami trzeba stworzyć na szybko mockowy bucket do użycia przez django-storages
            import boto3

            s3 = boto3.client("s3", region_name="us-east-1")
            s3.create_bucket(Bucket="test-bucket")
            yield
    finally:
        for key, previous_value in previous_env.items():
            if previous_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = previous_value


@pytest.fixture(autouse=True)
def mock_redis_connection(request):
    """Zastępuje wszystkie instancje Redis na FakeRedis w ramach testów.

    Dla testów integracyjnych (marker `integration`) mock jest wyłączony,
    bo testy mają korzystać z prawdziwego Redis.
    """

    if request.node.get_closest_marker("integration") is not None:
        yield
        return

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
