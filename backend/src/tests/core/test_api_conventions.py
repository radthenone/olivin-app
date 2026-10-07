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

    def test_not_in_installed_apps(self):
        """Nie ma jej w zainstalowanych aplikacjach."""
        assert "apps.analytics" not in settings.INSTALLED_APPS

    def test_no_app_config(self):
        """Nie ma konfiguracji aplikacji."""
        assert not apps.is_installed("apps.analytics")

    def test_no_code_in_repository(self):
        """Nie ma kodu w repozytorium."""
        assert not list((APPS_DIR / "analytics").glob("**/*.py"))

    def test_settings_and_urls_do_not_mention_analytics(self):
        """Ustawienia i routing nie wspominają `analytics`."""
        watched = [
            CORE_DIR / "settings" / "components" / "apps.py",
            CORE_DIR / "urls.py",
        ]
        for path in watched:
            assert "analytics" not in path.read_text(encoding="utf-8")


class TestPagination:
    """Paginacja numerowana: 24 na stronę, maksimum 100 przez `?page_size`."""

    def test_class_is_default(self):
        """Klasa paginacji jest domyślna."""
        assert (
            settings.REST_FRAMEWORK["DEFAULT_PAGINATION_CLASS"]
            == "core.api.pagination.StandardPagination"
        )

    def test_default_page_size(self):
        """Domyślny rozmiar strony to 24."""
        assert StandardPagination.page_size == 24
        assert settings.REST_FRAMEWORK["PAGE_SIZE"] == 24

    def test_client_can_request_smaller_page(self):
        """Klient może zażądać mniejszej strony."""
        assert _page_size_for({"page_size": "5"}) == 5

    def test_request_above_limit_is_capped_at_hundred(self):
        """Żądanie powyżej limitu jest przycinane do stu."""
        assert _page_size_for({"page_size": "500"}) == 100

    def test_without_param_default_applies(self):
        """Bez parametru obowiązuje wartość domyślna."""
        assert _page_size_for({}) == 24


@pytest.mark.django_db
class TestPaginationOnLiveEndpoint:
    """Ten sam kształt odpowiedzi na żywym endpoincie, nie tylko w klasie."""

    def test_list_has_pagination_envelope(self, authenticated_client: APIClient, user):
        """Lista ma kopertę paginacji."""
        ProfileFactory(user=user)

        response = cast(Response, authenticated_client.get(reverse("profile-list")))

        assert response.status_code == status.HTTP_200_OK
        assert set(response.data) >= {"count", "next", "previous", "results"}  # type: ignore

    def test_at_most_24_items_by_default(self, api_client: APIClient):
        """Domyślnie lista ma najwyżej 24 pozycje."""
        user = UserFactory()
        _fill_addresses(ProfileFactory(user=user))

        api_client.force_authenticate(user=user)
        response = cast(Response, api_client.get(reverse("address-list")))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == ADDRESSES_PER_PROFILE  # type: ignore
        assert len(response.data["results"]) == 24  # type: ignore
        assert response.data["next"] is not None  # type: ignore

    def test_page_size_narrows_page(self, api_client: APIClient):
        """`page_size` zawęża stronę."""
        user = UserFactory()
        _fill_addresses(ProfileFactory(user=user))

        api_client.force_authenticate(user=user)
        response = cast(
            Response, api_client.get(reverse("address-list"), {"page_size": 5})
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 5  # type: ignore


class TestOrdering:
    """Porządek modeli ma rozstrzygnięcie remisu — inaczej paginacja kłamie.

    Sprawdzamy sam porządek, a nie wynik paginacji na dwóch stronach: testy
    chodzą na SQLite, który przy remisie `created_at` i tak zwraca rekordy
    w stabilnej kolejności, więc taki test przechodziłby również bez poprawki.
    """

    def test_base_model_breaks_ties_by_id(self):
        """Model bazowy rozstrzyga remis identyfikatorem."""
        assert TimestampedModel._meta.ordering == ["-created_at", "-id"]

    @pytest.mark.parametrize("model", [Address, Profile])
    def test_account_models_inherit_same_ordering(self, model):
        """Modele kont dziedziczą ten sam porządek."""
        assert model._meta.ordering == ["-created_at", "-id"]


class TestCache:
    """Historia limitów musi być wspólna dla procesów, nie procesowa."""

    def test_default_cache_is_shared(self):
        """Domyślny cache jest współdzielony między procesami."""
        backend = cache_settings.CACHES["default"]["BACKEND"]
        assert backend == "django.core.cache.backends.redis.RedisCache"


class TestFilterBackends:
    """`django-filter` i `SearchFilter` są domyślne — widoki ich nie powtarzają."""

    def test_filter_backends(self):
        """Domyślne backendy filtrów."""
        assert settings.REST_FRAMEWORK["DEFAULT_FILTER_BACKENDS"] == (
            "django_filters.rest_framework.DjangoFilterBackend",
            "core.api.filters.SearchFilter",
        )

    def test_django_filters_is_installed(self):
        """`django_filters` jest zainstalowane."""
        assert "django_filters" in settings.INSTALLED_APPS

    def test_view_without_fields_does_not_announce_search(self):
        """Widok bez pól wyszukiwania nie ogłasza parametru `search`."""

        class ListWithoutSearch:
            pass

        assert SearchFilter().get_schema_operation_parameters(ListWithoutSearch()) == []

    def test_view_with_fields_announces_search(self):
        """Widok z polami wyszukiwania ogłasza parametr `search`."""

        class ListWithSearch:
            search_fields = ("name",)

        parameters = SearchFilter().get_schema_operation_parameters(ListWithSearch())

        assert [parameter["name"] for parameter in parameters] == ["search"]


class TestThrottling:
    """Limity żądań: anonim 60/min, zalogowany 300/min, zakres `auth` 10/min."""

    def test_rates(self):
        """Stawki limitów żądań."""
        assert settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] == {
            "anon": "60/min",
            "user": "300/min",
            "auth": "10/min",
        }

    def test_default_classes(self):
        """Domyślne klasy limitów żądań."""
        assert settings.REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] == (
            "rest_framework.throttling.AnonRateThrottle",
            "rest_framework.throttling.UserRateThrottle",
            "rest_framework.throttling.ScopedRateThrottle",
        )

    @pytest.mark.django_db
    def test_anonymous_gets_429_when_exceeded(self, api_client: APIClient):
        """Podmieniamy stawkę, żeby nie wysyłać 61 żądań dla jednej asercji."""

        def health() -> int:
            return cast(Response, api_client.get("/health/")).status_code

        with patch.dict(SimpleRateThrottle.THROTTLE_RATES, {"anon": "2/min"}):
            assert health() == status.HTTP_200_OK
            assert health() == status.HTTP_200_OK
            assert health() == status.HTTP_429_TOO_MANY_REQUESTS

    def test_auth_scope_applies_on_opted_in_view(self):
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

    def test_default_permission(self):
        """Domyślna permisja to `IsAuthenticated`."""
        assert settings.REST_FRAMEWORK["DEFAULT_PERMISSION_CLASSES"] == (
            "rest_framework.permissions.IsAuthenticated",
        )

    def test_allow_any_is_not_global(self):
        """`AllowAny` nie jest globalne."""
        assert (
            "rest_framework.permissions.AllowAny"
            not in (settings.REST_FRAMEWORK["DEFAULT_PERMISSION_CLASSES"])
        )

    def test_anonymous_cannot_access_accounts(self, api_client: APIClient):
        """Anonim nie wejdzie na konta."""
        response = cast(Response, api_client.get(reverse("profile-list")))
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_health_stays_open(self, api_client: APIClient):
        """Endpoint `health` zostaje otwarty."""
        response = cast(Response, api_client.get("/health/"))
        assert response.status_code == status.HTTP_200_OK
