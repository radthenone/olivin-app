"""Konwencje warstwy API, z których korzystają wszystkie aplikacje domenowe.

Te testy pilnują ustawień, a nie pojedynczego widoku. Rozjazd tutaj nie psuje
żadnej funkcji od razu — wychodzi dopiero, gdy nowy widok katalogu dziedziczy
inną paginację albo inny limit, niż zakłada klient.
"""

from __future__ import annotations

from typing import cast
from unittest.mock import patch

import pytest
from django.apps import apps
from django.conf import settings
from django.urls import reverse
from freezegun import freeze_time
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.test import APIClient, APIRequestFactory
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView

from apps.accounts.models import Address, Profile
from common import TimestampedModel
from core.api.filters import SearchFilter
from core.api.pagination import StandardPagination
from core.paths import APPS_DIR, CORE_DIR
from core.settings.components import cache as cache_settings
from tests.factories.accounts import ProfileFactory, UserFactory

ADDRESSES_PER_PROFILE = 30


def _fill_addresses(profile: Profile, count: int = ADDRESSES_PER_PROFILE) -> None:
    Address.objects.bulk_create(
        Address(
            profile=profile,
            street=f"Kwiatowa {index}",
            city="Kraków",
            postal_code="30-001",
            country="PL",
        )
        for index in range(count)
    )


def _page_size_for(query: dict[str, str]) -> int | None:
    request = Request(APIRequestFactory().get("/", query))
    return StandardPagination().get_page_size(request)


class TestAnalyticsAppRemoved:
    """`apps.analytics` była pustym szkieletem — po jej usunięciu nie ma śladu."""

    def test_nie_ma_w_zainstalowanych_aplikacjach(self):
        assert "apps.analytics" not in settings.INSTALLED_APPS

    def test_nie_ma_konfiguracji_aplikacji(self):
        assert not apps.is_installed("apps.analytics")

    def test_nie_ma_kodu_w_repozytorium(self):
        assert not list((APPS_DIR / "analytics").glob("**/*.py"))

    def test_ustawienia_i_urls_nie_wspominaja_analytics(self):
        watched = [
            CORE_DIR / "settings" / "components" / "apps.py",
            CORE_DIR / "urls.py",
        ]
        for path in watched:
            assert "analytics" not in path.read_text(encoding="utf-8")


class TestPagination:
    """Paginacja numerowana: 24 na stronę, maksimum 100 przez `?page_size`."""

    def test_klasa_jest_domyslna(self):
        assert (
            settings.REST_FRAMEWORK["DEFAULT_PAGINATION_CLASS"]
            == "core.api.pagination.StandardPagination"
        )

    def test_domyslny_rozmiar_strony(self):
        assert StandardPagination.page_size == 24
        assert settings.REST_FRAMEWORK["PAGE_SIZE"] == 24

    def test_klient_moze_zazadac_mniejszej_strony(self):
        assert _page_size_for({"page_size": "5"}) == 5

    def test_zadanie_powyzej_limitu_jest_przyciete_do_stu(self):
        assert _page_size_for({"page_size": "500"}) == 100

    def test_bez_parametru_obowiazuje_domyslna_wartosc(self):
        assert _page_size_for({}) == 24


@pytest.mark.django_db
class TestPaginationOnLiveEndpoint:
    """Ten sam kształt odpowiedzi na żywym endpoincie, nie tylko w klasie."""

    def test_lista_ma_koperte_paginacji(self, authenticated_client: APIClient, user):
        ProfileFactory(user=user)

        response = cast(Response, authenticated_client.get(reverse("profile-list")))

        assert response.status_code == status.HTTP_200_OK
        assert set(response.data) >= {"count", "next", "previous", "results"}  # type: ignore

    def test_domyslnie_najwyzej_24_pozycje(self, api_client: APIClient):
        user = UserFactory()
        _fill_addresses(ProfileFactory(user=user))

        api_client.force_authenticate(user=user)
        response = cast(Response, api_client.get(reverse("address-list")))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == ADDRESSES_PER_PROFILE  # type: ignore
        assert len(response.data["results"]) == 24  # type: ignore
        assert response.data["next"] is not None  # type: ignore

    def test_page_size_zaweza_strone(self, api_client: APIClient):
        user = UserFactory()
        _fill_addresses(ProfileFactory(user=user))

        api_client.force_authenticate(user=user)
        response = cast(
            Response, api_client.get(reverse("address-list"), {"page_size": 5})
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 5  # type: ignore

    def test_strony_nie_powtarzaja_rekordow_z_ta_sama_chwila_utworzenia(
        self, api_client: APIClient
    ):
        """`created_at` nie jest unikalny — bez rozstrzygnięcia remisu wynik
        paginacji zależy od kolejności, jaką akurat zwróci baza."""
        user = UserFactory()
        with freeze_time("2026-09-19 12:00:00"):
            _fill_addresses(ProfileFactory(user=user))

        api_client.force_authenticate(user=user)
        first = cast(Response, api_client.get(reverse("address-list")))
        second = cast(Response, api_client.get(reverse("address-list"), {"page": 2}))

        seen = [row["id"] for row in first.data["results"]]  # type: ignore
        seen += [row["id"] for row in second.data["results"]]  # type: ignore
        assert len(seen) == ADDRESSES_PER_PROFILE
        assert len(set(seen)) == ADDRESSES_PER_PROFILE


class TestOrdering:
    """Porządek modeli ma rozstrzygnięcie remisu — inaczej paginacja kłamie."""

    def test_model_bazowy_rozstrzyga_remis_identyfikatorem(self):
        assert TimestampedModel._meta.ordering == ["-created_at", "-id"]

    @pytest.mark.parametrize("model", [Address, Profile])
    def test_modele_kont_dziedzicza_ten_sam_porzadek(self, model):
        assert model._meta.ordering == ["-created_at", "-id"]


class TestCache:
    """Historia limitów musi być wspólna dla procesów, nie procesowa."""

    def test_domyslny_cache_jest_wspoldzielony(self):
        backend = cache_settings.CACHES["default"]["BACKEND"]
        assert backend == "django.core.cache.backends.redis.RedisCache"


class TestFilterBackends:
    """`django-filter` i `SearchFilter` są domyślne — widoki ich nie powtarzają."""

    def test_backendy_filtrow(self):
        assert settings.REST_FRAMEWORK["DEFAULT_FILTER_BACKENDS"] == (
            "django_filters.rest_framework.DjangoFilterBackend",
            "core.api.filters.SearchFilter",
        )

    def test_django_filters_jest_zainstalowane(self):
        assert "django_filters" in settings.INSTALLED_APPS

    def test_widok_bez_pol_nie_oglasza_parametru_search(self):
        class ListWithoutSearch:
            pass

        assert SearchFilter().get_schema_operation_parameters(ListWithoutSearch()) == []

    def test_widok_z_polami_oglasza_parametr_search(self):
        class ListWithSearch:
            search_fields = ("name",)

        parameters = SearchFilter().get_schema_operation_parameters(ListWithSearch())

        assert [parameter["name"] for parameter in parameters] == ["search"]


class TestThrottling:
    """Limity żądań: anonim 60/min, zalogowany 300/min, zakres `auth` 10/min."""

    def test_stawki(self):
        assert settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] == {
            "anon": "60/min",
            "user": "300/min",
            "auth": "10/min",
        }

    def test_klasy_domyslne(self):
        assert settings.REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] == (
            "rest_framework.throttling.AnonRateThrottle",
            "rest_framework.throttling.UserRateThrottle",
            "rest_framework.throttling.ScopedRateThrottle",
        )

    @pytest.mark.django_db
    def test_anonim_dostaje_429_po_przekroczeniu(self, api_client: APIClient):
        """Podmieniamy stawkę, żeby nie wysyłać 61 żądań dla jednej asercji."""

        def health() -> int:
            return cast(Response, api_client.get("/health/")).status_code

        with patch.dict(SimpleRateThrottle.THROTTLE_RATES, {"anon": "2/min"}):
            assert health() == status.HTTP_200_OK
            assert health() == status.HTTP_200_OK
            assert health() == status.HTTP_429_TOO_MANY_REQUESTS

    def test_zakres_auth_obowiazuje_na_widoku_ktory_go_wlaczy(self):
        """Zakres `auth` czeka gotowy — sam z siebie nie ogranicza niczego."""

        class CouponValidationView(APIView):
            permission_classes = []
            throttle_scope = "auth"

            def get(self, request):
                return Response({"ok": True})

        factory = APIRequestFactory()
        view = CouponValidationView.as_view()

        with patch.dict(SimpleRateThrottle.THROTTLE_RATES, {"auth": "1/min"}):
            assert view(factory.get("/")).status_code == status.HTTP_200_OK
            assert (
                view(factory.get("/")).status_code == status.HTTP_429_TOO_MANY_REQUESTS
            )


@pytest.mark.django_db
class TestPermissions:
    """`IsAuthenticated` zostaje domyślne; `AllowAny` wyłącznie na widoku."""

    def test_domyslna_permisja(self):
        assert settings.REST_FRAMEWORK["DEFAULT_PERMISSION_CLASSES"] == (
            "rest_framework.permissions.IsAuthenticated",
        )

    def test_allow_any_nie_jest_globalne(self):
        assert (
            "rest_framework.permissions.AllowAny"
            not in (settings.REST_FRAMEWORK["DEFAULT_PERMISSION_CLASSES"])
        )

    def test_anonim_nie_wejdzie_na_konta(self, api_client: APIClient):
        response = cast(Response, api_client.get(reverse("profile-list")))
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_health_zostaje_otwarty(self, api_client: APIClient):
        response = cast(Response, api_client.get("/health/"))
        assert response.status_code == status.HTTP_200_OK
