"""Widoki adresów klienta (`/customers/addresses/`)."""

from __future__ import annotations

from typing import cast

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from apps.accounts.models import Address
from tests.factories.accounts import ProfileFactory, UserFactory

pytestmark = pytest.mark.django_db


def make_address(profile, **fields) -> Address:
    return Address.objects.create(
        profile=profile,
        street=fields.pop("street", "ul. Polna 1"),
        city="Kraków",
        postal_code="30-001",
        country="PL",
        **fields,
    )


@pytest.fixture
def owner_profile():
    return ProfileFactory()


@pytest.fixture
def owner_client(api_client: APIClient, owner_profile) -> APIClient:
    api_client.force_authenticate(user=owner_profile.user)
    return api_client


@pytest.fixture
def stranger_address():
    """Adres należący do innego konta."""
    return make_address(ProfileFactory(), street="ul. Obca 9")


def detail_url(address: Address) -> str:
    return reverse("address-detail", args=[address.pk])


def set_default_url(address: Address) -> str:
    return reverse("address-set-default", args=[address.pk])


class TestAddressAnonymous:
    """Anonim nie ma dostępu do adresów."""

    @pytest.mark.parametrize(
        ("method", "url_name"),
        [("get", "address-list"), ("post", "address-list")],
    )
    def test_anonymous_is_rejected(self, api_client: APIClient, method, url_name):
        """Lista i tworzenie bez logowania dają 401/403."""
        response = cast(Response, getattr(api_client, method)(reverse(url_name)))

        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_anonymous_cannot_set_default(
        self, api_client: APIClient, stranger_address
    ):
        """`set-default` bez logowania daje 401/403 i nie zmienia flagi."""
        response = cast(Response, api_client.patch(set_default_url(stranger_address)))

        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )
        stranger_address.refresh_from_db()
        assert stranger_address.is_default is False


class TestAddressCreate:
    """Tworzenie adresu."""

    def test_address_goes_to_logged_in_profile(self, owner_client, owner_profile):
        """Nowy adres trafia do profilu zalogowanego użytkownika."""
        response = cast(
            Response,
            owner_client.post(
                reverse("address-list"),
                {"street": "ul. Nowa 5", "city": "Gdańsk", "country": "PL"},
            ),
        )

        assert response.status_code == status.HTTP_201_CREATED
        address = Address.objects.get(pk=response.data["id"])  # type: ignore[index]
        assert address.profile == owner_profile

    def test_user_without_profile_gets_400(self, api_client: APIClient):
        """Konto bez profilu nie może dodać adresu."""
        api_client.force_authenticate(user=UserFactory())

        response = cast(
            Response,
            api_client.post(reverse("address-list"), {"street": "ul. Nowa 5"}),
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert not Address.objects.exists()


class TestAddressIsolation:
    """Żaden użytkownik nie widzi ani nie zmienia adresu drugiego."""

    def test_list_shows_only_own_addresses(
        self, owner_client, owner_profile, stranger_address
    ):
        """Lista zawiera tylko adresy zalogowanego konta."""
        own = make_address(owner_profile)

        response = cast(Response, owner_client.get(reverse("address-list")))

        assert response.status_code == status.HTTP_200_OK
        ids = [row["id"] for row in response.data["results"]]  # type: ignore[index]
        assert ids == [str(own.pk)]

    @pytest.mark.parametrize(
        ("method", "payload"),
        [
            ("get", None),
            ("put", {"street": "ul. Przejęta 1"}),
            ("patch", {"street": "ul. Przejęta 1"}),
            ("delete", None),
        ],
    )
    def test_foreign_address_is_404(
        self, owner_client, stranger_address, method, payload
    ):
        """Odczyt, zmiana i usunięcie cudzego adresu dają 404 i nic nie zmieniają."""
        response = cast(
            Response,
            getattr(owner_client, method)(detail_url(stranger_address), payload),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        stranger_address.refresh_from_db()
        assert stranger_address.street == "ul. Obca 9"

    def test_foreign_address_cannot_become_default(
        self, owner_client, stranger_address
    ):
        """`set-default` na cudzym adresie daje 404."""
        response = cast(Response, owner_client.patch(set_default_url(stranger_address)))

        assert response.status_code == status.HTTP_404_NOT_FOUND
        stranger_address.refresh_from_db()
        assert stranger_address.is_default is False


class TestAddressSetDefault:
    """Profil ma dokładnie jeden adres domyślny."""

    def test_switches_default_to_chosen_address(self, owner_client, owner_profile):
        """Wybrany adres staje się domyślny, poprzedni traci flagę."""
        old = make_address(owner_profile, is_default=True)
        new = make_address(owner_profile)

        response = cast(Response, owner_client.patch(set_default_url(new)))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_default"] is True  # type: ignore[index]
        old.refresh_from_db()
        new.refresh_from_db()
        assert (old.is_default, new.is_default) == (False, True)

    def test_leaves_other_accounts_untouched(
        self, owner_client, owner_profile, stranger_address
    ):
        """Zmiana domyślnego adresu nie zdejmuje flagi z adresów innego konta."""
        stranger_address.is_default = True
        stranger_address.save()
        own = make_address(owner_profile)

        owner_client.patch(set_default_url(own))

        stranger_address.refresh_from_db()
        assert stranger_address.is_default is True

    def test_already_default_is_noop(self, owner_client, owner_profile):
        """Wywołanie na już domyślnym adresie nic nie zmienia."""
        default = make_address(owner_profile, is_default=True)
        other = make_address(owner_profile)

        response = cast(Response, owner_client.patch(set_default_url(default)))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_default"] is True  # type: ignore[index]
        assert list(Address.objects.filter(profile=owner_profile, is_default=True)) == [
            default
        ]
        other.refresh_from_db()
        assert other.is_default is False

    def test_failed_save_keeps_previous_default(
        self, owner_client, owner_profile, monkeypatch
    ):
        """Błąd zapisu nowego domyślnego adresu nie zostawia profilu bez domyślnego."""
        old = make_address(owner_profile, is_default=True)
        new = make_address(owner_profile)

        def broken_save(self, *args, **kwargs):
            raise RuntimeError("zapis padł")

        monkeypatch.setattr(Address, "save", broken_save)

        with pytest.raises(RuntimeError):
            owner_client.patch(set_default_url(new))

        old.refresh_from_db()
        assert old.is_default is True
