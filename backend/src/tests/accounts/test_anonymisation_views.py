"""Endpointy anonimizacji konta (#204): potwierdzenie hasłem albo kodem z maila."""

from __future__ import annotations

import re
from typing import cast
from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from apps.accounts.models import CustomUser
from apps.orders.models import OrderStatus
from tests.factories.accounts import UserFactory
from tests.factories.orders import OrderFactory

pytestmark = pytest.mark.django_db

MAIL = "apps.accounts.services.anonymisation_code.send_notification_email"
PASSWORD = "testpass123!"


def anonymise(client: APIClient, **payload: str) -> Response:
    return cast(
        Response, client.post(reverse("account-anonymise"), payload, format="json")
    )


def request_code(client: APIClient) -> Response:
    return cast(Response, client.post(reverse("account-anonymise-code")))


def is_anonymised(user: CustomUser) -> bool:
    user.refresh_from_db()
    return not user.is_active


@pytest.fixture
def password_user() -> CustomUser:
    return UserFactory(password=PASSWORD)


@pytest.fixture
def social_user() -> CustomUser:
    user = UserFactory(email="social@test.com")
    user.set_unusable_password()
    user.save()
    return user


def client_for(user: CustomUser) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def test_requires_authentication(api_client: APIClient) -> None:
    response = anonymise(api_client, password=PASSWORD)

    assert response.status_code in (
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    )


def test_anonymises_with_correct_password(password_user) -> None:
    response = anonymise(client_for(password_user), password=PASSWORD)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert is_anonymised(password_user)


@pytest.mark.parametrize("payload", [{}, {"password": "wrong-pass"}, {"code": "1"}])
def test_rejects_without_correct_password(password_user, payload) -> None:
    response = anonymise(client_for(password_user), **payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert not is_anonymised(password_user)


def test_refuses_with_order_in_progress(password_user) -> None:
    OrderFactory(user=password_user, status=OrderStatus.SHIPPED)

    response = anonymise(client_for(password_user), password=PASSWORD)

    assert response.status_code == status.HTTP_409_CONFLICT
    assert not is_anonymised(password_user)


def test_code_is_not_sent_to_account_with_password(password_user) -> None:
    with patch(MAIL) as mail:
        response = request_code(client_for(password_user))

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    mail.assert_not_called()


def _sent_code(
    client: APIClient, django_capture_on_commit_callbacks
) -> tuple[str, str]:
    with patch(MAIL) as mail, django_capture_on_commit_callbacks(execute=True):
        response = request_code(client)
    assert response.status_code == status.HTTP_202_ACCEPTED
    mail.assert_called_once()
    kwargs = mail.call_args.kwargs
    match = re.search(r"\b(\d{6})\b", kwargs["body"])
    assert match is not None
    return kwargs["to"], match.group(1)


def test_social_account_anonymises_with_emailed_code(
    social_user, django_capture_on_commit_callbacks
) -> None:
    client = client_for(social_user)
    to, code = _sent_code(client, django_capture_on_commit_callbacks)

    response = anonymise(client, code=code)

    assert to == "social@test.com"
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert is_anonymised(social_user)


def test_social_account_rejects_wrong_or_missing_code(
    social_user, django_capture_on_commit_callbacks
) -> None:
    client = client_for(social_user)
    assert anonymise(client, code="123456").status_code == 400
    _, code = _sent_code(client, django_capture_on_commit_callbacks)
    wrong = "000000" if code != "000000" else "111111"

    assert anonymise(client, code=wrong).status_code == 400
    assert anonymise(client, password="anything").status_code == 400
    assert not is_anonymised(social_user)


def test_code_is_invalidated_after_too_many_attempts(
    social_user, django_capture_on_commit_callbacks
) -> None:
    client = client_for(social_user)
    _, code = _sent_code(client, django_capture_on_commit_callbacks)
    wrong = "000000" if code != "000000" else "111111"
    for _ in range(5):
        anonymise(client, code=wrong)

    response = anonymise(client, code=code)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert not is_anonymised(social_user)


def test_code_is_not_resent_within_cooldown(
    social_user, django_capture_on_commit_callbacks
) -> None:
    client = client_for(social_user)
    _sent_code(client, django_capture_on_commit_callbacks)

    with patch(MAIL) as mail, django_capture_on_commit_callbacks(execute=True):
        response = request_code(client)

    assert response.status_code == status.HTTP_202_ACCEPTED
    mail.assert_not_called()


def test_order_is_checked_before_password(password_user) -> None:
    OrderFactory(user=password_user, status=OrderStatus.PAID)

    response = anonymise(client_for(password_user), password="wrong-pass")

    assert response.status_code == status.HTTP_409_CONFLICT


def test_active_order_does_not_burn_code(
    social_user, django_capture_on_commit_callbacks
) -> None:
    client = client_for(social_user)
    _, code = _sent_code(client, django_capture_on_commit_callbacks)
    order = OrderFactory(user=social_user, status=OrderStatus.SHIPPED)
    assert anonymise(client, code=code).status_code == status.HTTP_409_CONFLICT
    order.status = OrderStatus.DELIVERED
    order.save()

    response = anonymise(client, code=code)

    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_staff_account_is_refused(password_user) -> None:
    password_user.is_staff = True
    password_user.save()

    response = anonymise(client_for(password_user), password=PASSWORD)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert isinstance(cast(dict, response.data)["detail"], str)
    assert not is_anonymised(password_user)


def test_code_refusal_has_detail_message(password_user) -> None:
    response = request_code(client_for(password_user))

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert isinstance(cast(dict, response.data)["detail"], str)
