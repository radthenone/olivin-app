from __future__ import annotations

from typing import Protocol, cast

import pytest
from allauth.account.adapter import get_adapter
from django.contrib.auth import get_user_model
from rest_framework import status

from apps.accounts.models import CustomUser, Profile


class SignupFormStub:
    cleaned_data = {
        "email": "signup@test.com",
        "password1": "testpass123!",
    }


class PhoneNumberWithE164(Protocol):
    """Minimalny interfejs numeru telefonu zwracanego przez PhoneNumberField."""

    @property
    def as_e164(self) -> str: ...


@pytest.mark.django_db
def test_account_adapter_tworzy_profil_po_udanym_signupie(rf):
    """Signup przez allauth powinien założyć profil w tej samej operacji."""
    user_model = get_user_model()
    user = user_model()
    request = rf.post(
        "/",
        {
            "firstName": "Jan",
            "lastName": "Kowalski",
            "dateOfBirth": "1990-01-15",
            "phoneNumber": "+48500100200",
        },
    )

    saved_user = get_adapter().save_user(request, user, SignupFormStub())

    profile = Profile.objects.get(user=saved_user)
    assert profile.first_name == "Jan"
    assert profile.last_name == "Kowalski"
    assert profile.date_of_birth is not None
    assert profile.date_of_birth.isoformat() == "1990-01-15"
    assert cast(PhoneNumberWithE164, profile.phone_number).as_e164 == "+48500100200"


@pytest.mark.django_db
def test_headless_signup_tworzy_profil(api_client):
    """Rejestracja headless allauth powinna tworzyć użytkownika i profil."""
    response = api_client.post(
        "/_allauth/app/v1/auth/signup",
        {
            "email": "headless-signup@test.com",
            "password": "testpass123!",
            "firstName": "Anna",
            "lastName": "Nowak",
            "dateOfBirth": "1992-02-20",
            "phoneNumber": "+48500100201",
        },
        format="json",
    )

    assert response.status_code in {
        status.HTTP_200_OK,
        status.HTTP_401_UNAUTHORIZED,
    }
    user = CustomUser.objects.get(email="headless-signup@test.com")
    profile = Profile.objects.get(user=user)
    assert profile.first_name == "Anna"
    assert profile.last_name == "Nowak"
    assert profile.date_of_birth is not None
    assert profile.date_of_birth.isoformat() == "1992-02-20"
    assert cast(PhoneNumberWithE164, profile.phone_number).as_e164 == "+48500100201"
