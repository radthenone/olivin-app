from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status

# Globalny mark, by zezwolić wszystkim testom w tym pliku na kontakt z naszą testową bazą danych PostgreSQL (tą z tmpfs)
pytestmark = pytest.mark.django_db


def test_health_check_integration(client):
    """
    Testuje prawdziwe połączenia z zależnymi serwisami (Baza, Redis, S3).
    Dzięki postawieniu wyizolowanego środowiska i użyciu zmiennych z Twojego docker-compose,
    te usługi są w tej chwili tu dostępne "na żywo" do odpytania! Nie trzeba nic mockować w przypadku "happy path".
    """
    url = reverse("health_check")
    response = client.get(url, secure=True)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["status"] == "healthy", f"Coś nie wstało! {response.data}"
    assert response.data["services"]["database"] == "healthy"
    assert response.data["services"]["redis"] == "healthy"
    assert response.data["services"]["storage"] == "healthy"


@patch("core.utils.health.views.connection.cursor")
def test_health_check_database_unhealthy(mock_cursor, client):
    """
    W tym teście badamy sytuację awaryjną za pomocą Mockowania (z wbudowanej biblioteki unittest.mock).
    Zmuszamy wewnętrzne zapytanie kursora Postgresa do rzucenia wyjątkiem obojętnie co by się działo.
    """
    mock_cursor.side_effect = Exception("Database connection rejected")

    url = reverse("health_check")
    response = client.get(url, secure=True)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["status"] == "unhealthy"
    assert (
        "unhealthy: Database connection rejected"
        in response.data["services"]["database"]
    )
    # Zobacz, że mimo awarii bazy m.in. redis i minio potrafią działać niezależnie
    assert response.data["services"]["redis"] == "healthy"


@patch("core.utils.health.views.boto3.client")
def test_health_check_s3_unhealthy(mock_boto3, client):
    """
    Tutaj mockujemy awarię środowiska MinIO/AWS S3 wywalając import klasy klienta SDK.
    """
    mock_boto3.side_effect = Exception("Storage is down!")

    url = reverse("health_check")
    response = client.get(url, secure=True)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["status"] == "unhealthy"
    assert "unhealthy: Storage is down!" in response.data["services"]["storage"]
