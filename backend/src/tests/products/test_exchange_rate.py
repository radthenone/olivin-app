"""Kurs euro i ceny w euro dla klienta z Unii (`CONTEXT.md`, ExchangeRate; ADR 0019)."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import requests
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.products.models import ExchangeRate
from apps.products.pricing import price_in, round_up_to_half
from apps.products.services import activate_rate
from apps.products.tasks import refresh_exchange_rate
from common.money import Money
from core.integrations.exchange_rate import get_provider
from core.integrations.exchange_rate.fake import FakeExchangeRateProvider
from core.integrations.exchange_rate.nbp import NbpProvider
from tests.factories.products import (
    EngravableProductFactory,
    MetalRateFactory,
    ProductVariantFactory,
    PublishedProductFactory,
)


def euro_rate(rate: str = "4.000000", **kwargs: Any) -> ExchangeRate:
    kwargs.setdefault("effective_on", date(2026, 9, 1))
    return ExchangeRate.objects.create(
        currency="EUR", rate=Decimal(rate), source="test", **kwargs
    )


class TestRoundUpToHalf:
    """Cena w euro kończy się na ,00 albo ,50 — zawsze w górę."""

    @pytest.mark.parametrize(
        ("cents", "expected"),
        [(2500, 2500), (2501, 2550), (2550, 2550), (2551, 2600), (0, 0)],
    )
    def test_rounding(self, cents: int, expected: int):
        assert round_up_to_half(Money(cents, "EUR")) == Money(expected, "EUR")


@pytest.mark.django_db
class TestPriceIn:
    def test_price_is_converted_and_rounded_up(self):
        variant = ProductVariantFactory(price=10001)

        assert price_in(variant, euro_rate("4.000000")) == Money(2550, "EUR")

    def test_manual_price_takes_precedence(self):
        variant = ProductVariantFactory(price=40000, manual_price=20000)

        assert price_in(variant, euro_rate("4.000000")) == Money(5000, "EUR")

    def test_price_never_below_converted_cost_floor(self):
        """Cena złotowa nieaktualna wobec kursu kruszcu — próg wygrywa."""
        activate_rate(MetalRateFactory(price_per_gram=30000))
        # Koszt: 2 g × 300 zł = 600 zł; cena zapisana 500 zł jest poniżej.
        variant = ProductVariantFactory(
            product=PublishedProductFactory(),
            metal_weight_grams=Decimal("2.000"),
            price=50000,
        )

        # 600 zł / 4 = 150 € mimo że cena daje 125 €.
        assert price_in(variant, euro_rate("4.000000")) == Money(15000, "EUR")


@pytest.mark.django_db
class TestCurrentRate:
    def test_newest_rate_is_current_without_activation(self):
        euro_rate("4.300000", effective_on=date(2026, 8, 1))
        newer = euro_rate("4.250000", effective_on=date(2026, 9, 1))

        assert ExchangeRate.objects.current("EUR") == newer

    def test_no_rate_means_none(self):
        assert ExchangeRate.objects.current("EUR") is None


class TestAdapters:
    def test_registry_returns_configured_fake(self, settings):
        settings.EXCHANGE_RATE_PROVIDER = (
            "core.integrations.exchange_rate.fake.FakeExchangeRateProvider"
        )

        quote = get_provider().quote("EUR")

        assert quote.currency == "EUR"
        assert quote.base_currency == "PLN"
        assert quote.rate == FakeExchangeRateProvider.rate
        assert quote.source == "fake"

    def test_nbp_reads_mid_rate(self):
        response = MagicMock()
        response.json.return_value = {
            "table": "A",
            "code": "EUR",
            "rates": [
                {"no": "185/A/NBP/2026", "effectiveDate": "2026-09-24", "mid": 4.2651}
            ],
        }
        with patch(
            "core.integrations.exchange_rate.nbp.requests.get", return_value=response
        ) as get:
            quote = NbpProvider().quote("EUR")

        assert "/A/EUR/" in get.call_args.args[0]
        assert quote.rate == Decimal("4.2651")
        assert quote.quoted_on == date(2026, 9, 24)
        assert quote.source == "nbp"


@pytest.mark.django_db
class TestRefreshTask:
    def test_first_run_fetches_rate(self):
        assert refresh_exchange_rate() is True  # type: ignore[missing-argument]

        rate = ExchangeRate.objects.get()
        assert rate.rate == FakeExchangeRateProvider.rate
        assert rate.source == "fake"

    def test_rate_younger_than_30_days_is_kept(self):
        euro_rate(effective_on=timezone.localdate() - timedelta(days=29))

        assert refresh_exchange_rate() is False  # type: ignore[missing-argument]
        assert refresh_exchange_rate() is False  # type: ignore[missing-argument]
        assert ExchangeRate.objects.count() == 1

    def test_rate_quoted_30_days_ago_is_replaced(self, caplog):
        euro_rate("4.500000", effective_on=timezone.localdate() - timedelta(days=30))

        assert refresh_exchange_rate() is True  # type: ignore[missing-argument]
        current = ExchangeRate.objects.current("EUR")
        assert current is not None
        assert current.rate == FakeExchangeRateProvider.rate
        assert not [r for r in caplog.records if r.levelname == "ERROR"]

    def test_stale_rate_is_logged(self, caplog):
        euro_rate(effective_on=timezone.localdate() - timedelta(days=40))

        refresh_exchange_rate()  # type: ignore[missing-argument]

        assert any(r.levelname == "ERROR" for r in caplog.records)

    def test_network_errors_are_retried(self):
        assert requests.RequestException in refresh_exchange_rate.autoretry_for
        assert refresh_exchange_rate.max_retries

    def test_worker_start_queues_refresh(self):
        from core.celery import app, refresh_exchange_rate_on_start

        with patch.object(app, "send_task") as send:
            refresh_exchange_rate_on_start()

        send.assert_called_once_with("apps.products.tasks.refresh_exchange_rate")


def _get(client: APIClient, url: str, **params: Any) -> Any:
    response: Any = client.get(url, params or None)
    return response


@pytest.mark.django_db
class TestCatalogInEuro:
    def test_default_currency_is_pln(self, api_client: APIClient):
        euro_rate()
        product = PublishedProductFactory()
        ProductVariantFactory(product=product, price=10001)

        body = _get(api_client, reverse("product-list")).json()

        price = body["results"][0]["cheapestVariant"]["price"]
        assert price == {"amount": 10001, "currency": "PLN"}

    def test_eur_prices_are_converted(self, api_client: APIClient):
        euro_rate("4.000000")
        product = EngravableProductFactory(engraving_price=10001)
        ProductVariantFactory(product=product, price=10001)

        body = _get(
            api_client,
            reverse("product-detail", kwargs={"slug": product.slug}),
            currency="EUR",
        ).json()

        assert body["variants"][0]["price"] == {"amount": 2550, "currency": "EUR"}
        assert body["engravingPrice"] == {"amount": 2550, "currency": "EUR"}

    def test_list_in_eur(self, api_client: APIClient):
        euro_rate("4.000000")
        ProductVariantFactory(product=PublishedProductFactory(), price=10000)

        body = _get(api_client, reverse("product-list"), currency="EUR").json()

        price = body["results"][0]["cheapestVariant"]["price"]
        assert price == {"amount": 2500, "currency": "EUR"}

    def test_eur_without_rate_is_rejected(self, api_client: APIClient):
        response = _get(api_client, reverse("product-list"), currency="EUR")

        assert response.status_code == 400

    def test_unknown_currency_is_rejected(self, api_client: APIClient):
        response = _get(api_client, reverse("product-list"), currency="USD")

        assert response.status_code == 400

    def test_metal_rates_are_loaded_once(self, api_client: APIClient):
        """Próg kosztu w euro nie pyta o kurs kruszcu osobno dla każdego wariantu."""
        euro_rate()
        activate_rate(MetalRateFactory(price_per_gram=30000))
        for _ in range(5):
            ProductVariantFactory(product=PublishedProductFactory(), price=100000)
        with patch(
            "apps.products.models.metal_rate.MetalRateQuerySet.active_for"
        ) as per_variant:
            response = _get(api_client, reverse("product-list"), currency="EUR")

        assert response.status_code == 200
        per_variant.assert_not_called()


@pytest.mark.django_db
class TestCheckoutPreviewInEuro:
    """Koszyk i dostawa w euro liczone tą samą funkcją co zamówienie (ADR 0019)."""

    def test_cart_in_euro(self, api_client: APIClient, user):
        from apps.orders.services.cart import add_item
        from tests.factories.orders import CartFactory
        from tests.factories.products import stock

        euro_rate("4.000000")
        cart = CartFactory(user=user)
        variant = ProductVariantFactory(product=PublishedProductFactory(), price=10001)
        stock(variant, 5)
        add_item(cart, variant=variant, quantity=2)
        api_client.force_authenticate(user)

        body = _get(api_client, reverse("cart-detail"), currency="EUR").json()

        item = body["items"][0]
        assert item["unitPrice"] == {"amount": 2550, "currency": "EUR"}
        assert item["lineTotal"] == {"amount": 5100, "currency": "EUR"}
        assert body["total"] == {"amount": 5100, "currency": "EUR"}

    def test_shipping_cost_in_euro(self, api_client: APIClient):
        from apps.shipping.models import ShippingZone
        from tests.factories.shipping import ShippingMethodFactory

        euro_rate("4.000000")
        ShippingMethodFactory(zone=ShippingZone.EU, rate=8001)

        body = _get(
            api_client, reverse("shipping-method-list"), zone="EU", currency="EUR"
        ).json()

        assert body[0]["cost"] == {"amount": 2001, "currency": "EUR"}


@pytest.mark.django_db
def test_sales_document_prints_rate_and_quote_date():
    from django.template.loader import render_to_string

    from tests.factories.orders import OrderFactory

    order = OrderFactory(
        currency="EUR",
        exchange_rate=Decimal("4.265100"),
        exchange_rate_on=date(2026, 9, 24),
        exchange_rate_source="nbp",
    )

    html = render_to_string(
        "orders/sales_document.html",
        {"document": None, "order": order, "items": [], "seller": {}},
    )

    assert "NBP z dnia 2026-09-24" in html
    assert "1 EUR = 4.265100 PLN" in html
