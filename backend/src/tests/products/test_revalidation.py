"""Rewalidacja keszu katalogu na webie po zapisie produktu i przeliczeniu cen (#318, ADR 0034)."""

from __future__ import annotations

from typing import Any, cast
from unittest.mock import patch

import pytest
import requests

from apps.products.models import Product, ProductVariant
from apps.products.services import activate_rate
from apps.products.tasks import recalculate_variant_prices
from core.integrations.web_revalidation import (
    SECRET_HEADER,
    WebRevalidationTransientError,
    revalidate_tags,
)
from tests.factories.products import (
    MetalRateFactory,
    ProductFactory,
    ProductVariantFactory,
    PublishedProductFactory,
)

POST = "core.integrations.web_revalidation.requests.post"
SECRET = "test-revalidate-secret"


@pytest.fixture
def revalidate_settings(settings):
    """Web pod znanym adresem i ustawiony sekret rewalidacji."""
    settings.FRONTEND_URL = "https://olivin.example"
    settings.REVALIDATE_SECRET = SECRET
    return settings


def _sent_tags(post) -> list[list[str]]:
    return [call.kwargs["json"]["tags"] for call in post.call_args_list]


class TestRevalidateTags:
    """Klient HTTP rewalidacji: adres, sekret, timeout i klasyfikacja błędów."""

    def test_posts_tags_with_secret_header(self, revalidate_settings):
        """POST na `{FRONTEND_URL}/api/revalidate` z sekretem w nagłówku i tagami w treści."""
        with patch(POST) as post:
            assert revalidate_tags(["catalog"]) is True

        post.assert_called_once()
        assert post.call_args.args[0] == "https://olivin.example/api/revalidate"
        assert post.call_args.kwargs["json"] == {"tags": ["catalog"]}
        assert post.call_args.kwargs["headers"][SECRET_HEADER] == SECRET
        assert post.call_args.kwargs["timeout"] > 0

    def test_without_secret_does_nothing(self, settings):
        """Brak sekretu (dev, testy) → żadnego żądania do webu."""
        settings.REVALIDATE_SECRET = ""
        with patch(POST) as post:
            assert revalidate_tags(["catalog"]) is False

        post.assert_not_called()

    def test_timeout_is_transient(self, revalidate_settings):
        """Timeout webu to błąd przejściowy — zadanie ponowi go z odstępem."""
        with patch(POST, side_effect=requests.Timeout("web śpi")):
            with pytest.raises(WebRevalidationTransientError):
                revalidate_tags(["catalog"])

    def test_server_error_is_transient(self, revalidate_settings):
        """5xx webu to błąd przejściowy."""
        response = requests.Response()
        response.status_code = 503
        with patch(POST, return_value=response):
            with pytest.raises(WebRevalidationTransientError):
                revalidate_tags(["catalog"])

    def test_rejected_secret_is_logged_not_retried(self, revalidate_settings, caplog):
        """401 (zły sekret) nie jest przejściowy: log błędu, bez ponawiania."""
        response = requests.Response()
        response.status_code = 401
        with patch(POST, return_value=response):
            assert revalidate_tags(["catalog"]) is False

        assert "401" in caplog.text


@pytest.mark.django_db
class TestProductSaveRevalidation:
    """Zapis produktu wysyła tag `product:<slug>` dopiero po zatwierdzeniu transakcji."""

    def test_publication_sends_product_tag_after_commit(
        self, revalidate_settings, django_capture_on_commit_callbacks
    ):
        """Publikacja: przed commitem cisza, po commicie tag produktu."""
        with patch(POST) as post:
            with django_capture_on_commit_callbacks(execute=True):
                product = PublishedProductFactory()
                assert not post.called

        assert _sent_tags(post) == [[f"product:{product.slug}"]]

    def test_edit_of_published_product_sends_product_tag(
        self, revalidate_settings, django_capture_on_commit_callbacks
    ):
        """Zwykła edycja opublikowanego produktu też odświeża jego stronę."""
        product = PublishedProductFactory()
        with patch(POST) as post:
            with django_capture_on_commit_callbacks(execute=True):
                product.name = "Nowa nazwa"
                product.save()

        assert _sent_tags(post) == [[f"product:{product.slug}"]]

    def test_draft_without_slug_sends_nothing(
        self, revalidate_settings, django_capture_on_commit_callbacks
    ):
        """Szkic bez adresu nie ma strony na webie — nie ma czego odświeżać."""
        with patch(POST) as post:
            with django_capture_on_commit_callbacks(execute=True):
                ProductFactory()

        post.assert_not_called()

    def test_web_timeout_does_not_break_save(
        self, revalidate_settings, django_capture_on_commit_callbacks
    ):
        """Timeout webu nie przerywa zapisu — produkt zostaje zapisany."""
        with patch(POST, side_effect=requests.Timeout("web śpi")) as post:
            with django_capture_on_commit_callbacks(execute=True):
                product = PublishedProductFactory()

        assert post.called
        assert Product.objects.filter(pk=product.pk).exists()


@pytest.mark.django_db
class TestRecalculationRevalidation:
    """Przeliczenie cen po aktywacji kursu wysyła tag `catalog`."""

    def test_recalculate_variant_prices_sends_catalog_tag(
        self, revalidate_settings, django_capture_on_commit_callbacks
    ):
        """Zmiana cen wariantów → tag `catalog` po przeliczeniu."""
        rate = MetalRateFactory(price_per_gram=30000)
        activate_rate(rate)
        variant: ProductVariant = ProductVariantFactory(
            product=PublishedProductFactory(), price=1
        )

        with patch(POST) as post:
            with django_capture_on_commit_callbacks(execute=True):
                changed = cast(Any, recalculate_variant_prices)(
                    rate.metal, rate.fineness
                )

        assert changed >= 1
        variant.refresh_from_db()
        assert variant.price != 1
        assert ["catalog"] in _sent_tags(post)
