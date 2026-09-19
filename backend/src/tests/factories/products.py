from __future__ import annotations

from decimal import Decimal

from factory.declarations import Sequence, SubFactory, Trait
from factory.django import DjangoModelFactory

from apps.products.models import (
    Fineness,
    Material,
    MetalColor,
    Product,
    ProductStatus,
    ProductVariant,
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
