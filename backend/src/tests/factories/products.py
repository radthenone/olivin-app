from __future__ import annotations

from datetime import date
from decimal import Decimal

from factory.declarations import Sequence, SubFactory, Trait
from factory.django import DjangoModelFactory

from apps.products.models import (
    CostComponent,
    Fineness,
    Material,
    MetalColor,
    MetalRate,
    MetalRateStatus,
    Product,
    ProductStatus,
    ProductVariant,
)
from apps.inventory.models import (
    InventoryItem,
    StockMovement,
    StockMovementReason,
)
from tests.factories.categories import CategoryFactory


class ProductFactory(DjangoModelFactory):
    """Fabryka dla modelu Product — domyślnie szkic, jak po założeniu w panelu."""

    class Meta:
        model = Product

    name = Sequence(lambda n: f"Produkt {n}")
    description = "Opis produktu"
    category = SubFactory(CategoryFactory)
    material = Material.GOLD
    fineness = Fineness.F585
    status = ProductStatus.DRAFT
    is_made_to_order = False
    production_time_days = None


class PublishedProductFactory(ProductFactory):
    status = ProductStatus.PUBLISHED


class MadeToOrderProductFactory(ProductFactory):
    """Obrączki: wytwarzane po złożeniu zamówienia, z czasem realizacji."""

    status = ProductStatus.PUBLISHED
    is_made_to_order = True
    production_time_days = 21


class ProductVariantFactory(DjangoModelFactory):
    """Fabryka dla modelu ProductVariant — domyślnie ze stawką podatku.

    Zwolnienie jest cechą (`vat_exempt=True`), a nie osobną podklasą: trzy
    pola muszą zmienić się razem, bo inaczej nie przejdą ani walidacji modelu,
    ani ograniczenia w bazie (ADR 0013).
    """

    class Meta:
        model = ProductVariant

    class Params:
        vat_exempt = Trait(
            vat_rate=None,
            is_vat_exempt=True,
            vat_exemption_basis=("art. 122 ust. 1 ustawy o podatku od towarów i usług"),
        )

    product = SubFactory(ProductFactory)
    sku = Sequence(lambda n: f"SKU-{n:05d}")
    metal_color = MetalColor.YELLOW
    size = ""
    length = ""
    stone = ""
    metal_weight_grams = Decimal("3.500")
    price = 129900
    manual_price = None
    currency = "PLN"
    vat_rate = Decimal("0.2300")
    is_vat_exempt = False
    vat_exemption_basis = ""


class MetalRateFactory(DjangoModelFactory):
    """Fabryka dla modelu MetalRate — domyślnie kurs zaproponowany.

    Aktywny kurs powstaje przez `activate_rate()`, a nie przez ustawienie
    pola: inaczej test przechodziłby ścieżką, której w panelu nie ma.
    """

    class Meta:
        model = MetalRate

    metal = Material.GOLD
    fineness = Fineness.F585
    price_per_gram = 30000
    currency = "PLN"
    quoted_on = date(2026, 9, 1)
    source = "manual"
    status = MetalRateStatus.PROPOSED


class CostComponentFactory(DjangoModelFactory):
    """Fabryka dla modelu CostComponent."""

    class Meta:
        model = CostComponent

    variant = SubFactory(ProductVariantFactory)
    name = Sequence(lambda n: f"Robocizna {n}")
    amount = 5000
    currency = "PLN"


class InventoryItemFactory(DjangoModelFactory):
    """Fabryka stanu magazynowego. Stan ustawia się ruchem, nie polem."""

    class Meta:
        model = InventoryItem

    variant = SubFactory(ProductVariantFactory)
    reserved = 0


class StockMovementFactory(DjangoModelFactory):
    """Fabryka ruchu magazynowego."""

    class Meta:
        model = StockMovement

    item = SubFactory(InventoryItemFactory)
    quantity = 10
    reason = StockMovementReason.DELIVERY
    note = ""


def stock(variant, quantity: int, reserved: int = 0) -> InventoryItem:
    """Wariant ze stanem: jeden ruch przyjęcia i ewentualna rezerwacja."""
    item = InventoryItemFactory(variant=variant, reserved=reserved)
    if quantity:
        StockMovementFactory(item=item, quantity=quantity)
    return item
