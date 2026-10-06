"""API newslettera: zapis, potwierdzenie, wypis — bez logowania (#203)."""

from __future__ import annotations

import datetime
from typing import Any
from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.consents.models import ConsentKind
from apps.notifications.models import NewsletterStatus, NewsletterSubscription
from tests.factories.consents import ConsentDocumentFactory

MAIL = "apps.notifications.newsletter.send_notification_email"


@pytest.fixture
def marketing_document():
    return ConsentDocumentFactory(
        kind=ConsentKind.MARKETING,
        version="2026-01",
        effective_from=datetime.date(2026, 1, 1),
    )


def _post(client: APIClient, name: str, data: dict) -> Any:
    """Odpowiedź klienta testowego — `Any`, bo ma `.json()`, którego `Response` nie zna."""
    return client.post(reverse(name), data, format="json")


@pytest.mark.django_db
class TestSubscribeEndpoint:
    def test_new_and_existing_address_get_identical_response(
        self, api_client: APIClient, marketing_document
    ):
        NewsletterSubscription.objects.create(
            email="known@test.com", status=NewsletterStatus.ACTIVE
        )

        with patch(MAIL):
            new = _post(api_client, "newsletter-subscribe", {"email": "new@test.com"})
            known = _post(
                api_client, "newsletter-subscribe", {"email": "known@test.com"}
            )

        assert new.status_code == status.HTTP_202_ACCEPTED
        assert known.status_code == new.status_code
        assert known.json() == new.json()
        assert NewsletterSubscription.objects.get(email="new@test.com").status == (
            NewsletterStatus.PENDING
        )

    def test_invalid_email_is_rejected(self, api_client: APIClient, marketing_document):
        response = _post(api_client, "newsletter-subscribe", {"email": "nope"})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_without_marketing_document_returns_400(self, api_client: APIClient):
        response = _post(api_client, "newsletter-subscribe", {"email": "a@test.com"})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert not NewsletterSubscription.objects.exists()


@pytest.mark.django_db
class TestConfirmAndUnsubscribeEndpoints:
    def test_confirm_activates(self, api_client: APIClient):
        subscription = NewsletterSubscription.objects.create(email="a@test.com")

        response = _post(
            api_client,
            "newsletter-confirm",
            {"token": str(subscription.confirmation_token)},
        )

        assert response.status_code == status.HTTP_200_OK
        subscription.refresh_from_db()
        assert subscription.status == NewsletterStatus.ACTIVE

    def test_confirm_unknown_token_returns_404(self, api_client: APIClient):
        response = _post(api_client, "newsletter-confirm", {"token": "bogus"})

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_unsubscribe_works_without_login(self, api_client: APIClient):
        subscription = NewsletterSubscription.objects.create(
            email="a@test.com", status=NewsletterStatus.ACTIVE
        )

        response = _post(
            api_client,
            "newsletter-unsubscribe",
            {"token": str(subscription.unsubscribe_token)},
        )

        assert response.status_code == status.HTTP_200_OK
        subscription.refresh_from_db()
        assert subscription.status == NewsletterStatus.UNSUBSCRIBED

    def test_unsubscribe_unknown_token_returns_404(self, api_client: APIClient):
        response = _post(api_client, "newsletter-unsubscribe", {"token": "bogus"})

        assert response.status_code == status.HTTP_404_NOT_FOUND
