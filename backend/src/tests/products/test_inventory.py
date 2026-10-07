"""Stan magazynowy i dostępność widoczna na wariancie."""

from __future__ import annotations

from typing import Any

import pytest
from django.db.utils import IntegrityError
from django.urls import reverse

from apps.inventory.models import (
    AVAILABLE,
    LOW_STOCK_THRESHOLD,
    ON_HAND,
    StockMovementReason,
)
from tests.factories.categories import CategoryFactory
from tests.factories.inventory import ReservationFactory
from tests.factories.products import (
    InventoryItemFactory,
    MadeToOrderProductFactory,
    ProductVariantFactory,
    PublishedProductFactory,
    StockMovementFactory,
    stock,
)


def _detail(client, slug: str | None) -> dict[str, Any]:
    response: Any = client.get(reverse("product-detail", kwargs={"slug": slug}))
    assert response.status_code == 200, response.content
    return response.json()


def _names(client, **params: Any) -> list[str]:
    response: Any = client.get(reverse("product-list"), params or None)
    assert response.status_code == 200, response.content
    return [row["name"] for row in response.json()["results"]]


@pytest.mark.django_db
class TestStockIsSumOfMovements:
    """Stan jest sumą ruchów, nie polem nadpisywanym."""

    def test_single_delivery(self):
        """Pojedyncza dostawa."""
        item = InventoryItemFactory()
        StockMovementFactory(item=item, quantity=7)

        assert item.on_hand == 7

    def test_movements_add_up(self):
        """Ruchy się sumują."""
        item = InventoryItemFactory()
        StockMovementFactory(item=item, quantity=10)
        StockMovementFactory(item=item, quantity=-3, reason=StockMovementReason.SALE)
        StockMovementFactory(item=item, quantity=1, reason=StockMovementReason.RETURN)

        assert item.on_hand == 8

    def test_no_movements_is_zero(self):
        """Brak ruchów to zero."""
        assert InventoryItemFactory().on_hand == 0

    def test_available_is_stock_minus_reservations(self):
        """Dostępne to stan minus rezerwacje."""
        item = InventoryItemFactory()
        StockMovementFactory(item=item, quantity=10)
        ReservationFactory(variant=item.variant, quantity=2)

        assert item.available == 8

    def test_correction_keeps_history(self):
        """Korektę robi się kolejnym ruchem, a nie edycją poprzedniego —
        inaczej historia przestaje tłumaczyć dzisiejszy stan."""
        item = InventoryItemFactory()
        StockMovementFactory(item=item, quantity=10)
        StockMovementFactory(
            item=item, quantity=-4, reason=StockMovementReason.CORRECTION
        )

        assert item.movements.count() == 2  # type: ignore[missing-attribute]
        assert item.on_hand == 6

    def test_zero_movement_is_rejected(self):
        """Ruch zerowy jest odrzucany."""
        item = InventoryItemFactory()

        with pytest.raises(IntegrityError):
            StockMovementFactory(item=item, quantity=0)

    def test_annotation_matches_property(self):
        """Adnotacja liczy to samo co właściwość."""
        from apps.inventory.models import InventoryItem

        item = InventoryItemFactory()
        StockMovementFactory(item=item, quantity=5)
        ReservationFactory(variant=item.variant, quantity=1)

        annotated = InventoryItem.objects.with_stock().get(pk=item.pk)

        assert getattr(annotated, ON_HAND) == item.on_hand
        assert getattr(annotated, AVAILABLE) == item.available


@pytest.mark.django_db
class TestVariantAvailability:
    """Dostępność liczona na wariancie."""

    def test_variant_with_stock_is_available(self):
        """Wariant ze stanem jest dostępny."""
        variant = ProductVariantFactory()
        stock(variant, 5)

        variant.refresh_from_db()
        assert variant.available == 5
        assert variant.is_available

    def test_variant_without_inventory_record_is_unavailable(self):
        """Wariant bez rekordu magazynu jest niedostępny."""
        variant = ProductVariantFactory()

        assert variant.available == 0
        assert not variant.is_available

    def test_variant_with_zero_stock_stays_but_unavailable(self):
        """Wariant z zerowym stanem nie znika, tylko jest niedostępny."""
        variant = ProductVariantFactory()
        stock(variant, 0)

        variant.refresh_from_db()
        assert variant.available == 0
        assert not variant.is_available

    def test_reservation_reduces_availability(self):
        """Rezerwacja zdejmuje z dostępności."""
        variant = ProductVariantFactory()
        stock(variant, 5, reserved=5)

        variant.refresh_from_db()
        assert variant.available == 0
        assert not variant.is_available

    @pytest.mark.parametrize(
        ("quantity", "expected"),
        [(0, False), (1, True), (3, True), (4, False), (10, False)],
    )
    def test_last_items_at_threshold(self, quantity: int, expected: bool):
        """Ostatnie sztuki przy progu."""
        variant = ProductVariantFactory()
        stock(variant, quantity)

        variant.refresh_from_db()
        assert variant.is_low_stock is expected

    def test_threshold_is_three_items(self):
        """Próg to trzy sztuki."""
        assert LOW_STOCK_THRESHOLD == 3


@pytest.mark.django_db
class TestMadeToOrderHasNoStock:
    """Produkt na zamówienie nie ma stanu i jest dostępny zawsze (ADR 0024)."""

    def test_has_no_item_count(self):
        """Nie ma liczby sztuk."""
        product = MadeToOrderProductFactory()
        variant = ProductVariantFactory(product=product)

        assert variant.available is None

    def test_is_available_without_stock(self):
        """Jest dostępny mimo braku stanu."""
        product = MadeToOrderProductFactory()
        variant = ProductVariantFactory(product=product)

        assert variant.is_available

    def test_is_never_last_items(self):
        """Nie bywa ostatnimi sztukami."""
        product = MadeToOrderProductFactory()
        variant = ProductVariantFactory(product=product)

        assert not variant.is_low_stock


@pytest.mark.django_db
class TestAvailabilityInApi:
    """Odwiedzający widzi dostępność na wariancie."""

    def test_variant_has_three_fields(self, api_client):
        """Wariant niesie trzy pola dostępności."""
        product = PublishedProductFactory()
        variant = ProductVariantFactory(product=product)
        stock(variant, 2)

        body = _detail(api_client, product.slug)

        assert body["variants"][0]["available"] == 2
        assert body["variants"][0]["isAvailable"] is True
        assert body["variants"][0]["isLowStock"] is True

    def test_unavailable_variant_stays_in_response(self, api_client):
        """Wariant bez stanu nie znika — jest widoczny jako niedostępny."""
        product = PublishedProductFactory()
        ProductVariantFactory(product=product, sku="BRAK")

        body = _detail(api_client, product.slug)

        assert [v["sku"] for v in body["variants"]] == ["BRAK"]
        assert body["variants"][0]["isAvailable"] is False

    def test_made_to_order_product_has_no_item_count(self, api_client):
        """Produkt na zamówienie nie ma liczby sztuk."""
        product = MadeToOrderProductFactory()
        ProductVariantFactory(product=product)

        body = _detail(api_client, product.slug)

        assert body["variants"][0]["available"] is None
        assert body["variants"][0]["isAvailable"] is True

    def test_cheapest_variant_on_list_has_availability(self, api_client):
        """Najtańszy wariant na liście też niesie dostępność."""
        product = PublishedProductFactory()
        variant = ProductVariantFactory(product=product)
        stock(variant, 1)

        response: Any = api_client.get(reverse("product-list"))
        cheapest = response.json()["results"][0]["cheapestVariant"]

        assert cheapest["available"] == 1
        assert cheapest["isLowStock"] is True


@pytest.mark.django_db
class TestUnavailableProductsGoLast:
    """Produkt bez dostępnych wariantów trafia na koniec każdego sortowania."""

    @pytest.fixture
    def catalog(self):
        """Katalog z produktami dostępnymi i niedostępnymi."""
        category = CategoryFactory()
        available = PublishedProductFactory(name="Dostepny", category=category)
        ProductVariantFactory(product=available, sku="A-1", price=200000)
        stock(available.variants.first(), 5)  # type: ignore[missing-attribute]

        empty = PublishedProductFactory(name="Pusty", category=category)
        ProductVariantFactory(product=empty, sku="B-1", price=100000)

        return {"available": available, "empty": empty}

    @pytest.mark.parametrize("ordering", ["price", "-price", "newest", "name", "-name"])
    def test_unavailable_always_last(self, api_client, catalog, ordering: str):
        """Niedostępny zawsze na końcu."""
        names = _names(api_client, ordering=ordering)

        assert names[-1] == "Pusty"

    def test_unavailable_stays_on_list(self, api_client, catalog):
        """Niedostępny nie znika z listy."""
        assert sorted(_names(api_client)) == ["Dostepny", "Pusty"]

    def test_made_to_order_counts_as_available(self, api_client):
        """Produkt na zamówienie liczy się jako dostępny."""
        category = CategoryFactory()
        made = MadeToOrderProductFactory(name="Obraczki", category=category)
        ProductVariantFactory(product=made, sku="M-1", price=300000)
        empty = PublishedProductFactory(name="Pusty", category=category)
        ProductVariantFactory(product=empty, sku="E-1", price=100000)

        assert _names(api_client, ordering="price") == ["Obraczki", "Pusty"]

    def test_product_with_one_available_variant_counts_as_available(self, api_client):
        """Produkt z jednym dostępnym wariantem liczy się jako dostępny."""
        category = CategoryFactory()
        mixed = PublishedProductFactory(name="Czesciowy", category=category)
        ProductVariantFactory(product=mixed, sku="C-1", price=100000)
        second = ProductVariantFactory(product=mixed, sku="C-2", price=200000)
        stock(second, 3)
        empty = PublishedProductFactory(name="Pusty", category=category)
        ProductVariantFactory(product=empty, sku="E-1", price=50000)

        assert _names(api_client, ordering="price") == ["Czesciowy", "Pusty"]


@pytest.mark.django_db
class TestNoWriteApi:
    """Magazyn prowadzi panel — API go nie wystawia (ADR 0021)."""

    def test_no_inventory_endpoint(self, authenticated_client):
        """Nie ma adresu magazynu w API."""
        from django.urls.exceptions import NoReverseMatch

        with pytest.raises(NoReverseMatch):
            reverse("inventoryitem-list")
