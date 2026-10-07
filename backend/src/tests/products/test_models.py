from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

from apps.products.models import (
    EFFECTIVE_PRICE,
    Product,
    ProductStatus,
    ProductVariant,
)
from common.money import Money
from tests.factories.categories import CategoryFactory
from tests.factories.products import (
    EngravableProductFactory,
    MadeToOrderProductFactory,
    ProductFactory,
    ProductVariantFactory,
    PublishedProductFactory,
)


@pytest.mark.django_db
class TestProductSlug:
    """Slug produktu zamraża się przy publikacji, nie przy pierwszym zapisie."""

    def test_draft_has_no_slug_yet(self):
        """Adres powstaje przy publikacji (`.ai/project.md`) — szkic nie ma
        go pod czym wyświetlić, a angielska nazwa nie musi jeszcze istnieć."""
        product = ProductFactory(name="Pierścionek")

        assert product.slug is None

    def test_many_drafts_coexist_without_slugs(self):
        """Kolumna sluga jest unikalna, więc pusty adres musi być `NULL`,
        a nie pustym łańcuchem — dwa puste łańcuchy by się zderzyły."""
        first = ProductFactory(name="Pierwszy")
        second = ProductFactory(name="Drugi")

        assert first.slug is None
        assert second.slug is None
        assert Product.objects.filter(slug__isnull=True).count() == 2

    def test_publishing_sets_slug_from_english_name(self):
        """Publikacja nadaje adres z angielskiego brzmienia nazwy."""
        product = PublishedProductFactory(name="Pierścionek")

        assert product.slug == "en-pierscionek"

    def test_polish_name_is_not_used_in_slug(self):
        """Polska nazwa nie trafia wprost do adresu."""
        product = PublishedProductFactory(name="Łańcuszek złoty")

        assert product.slug != "lancuszek-zloty"

    def test_collision_gets_suffix(self):
        """Kolizja slugów dostaje przyrostek."""
        PublishedProductFactory(name="Ring")
        second = PublishedProductFactory(name="Ring")

        assert second.slug == "en-ring-2"

    def test_draft_can_still_be_edited(self):
        """Szkic wolno jeszcze poprawić."""
        product = ProductFactory(name="Gold ring", slug="gold-ring")

        product.slug = "golden-ring"
        product.save()

        product.refresh_from_db()
        assert product.slug == "golden-ring"

    def test_manual_slug_survives_publishing(self, settings):
        """Wpisany adres ma pierwszeństwo i nie rusza silnika — to jedyna
        droga działająca bez sieci."""
        product = ProductFactory(name="Pierścionek", slug="engagement-ring")
        settings.TRANSLATION_PROVIDER = "tests.shared.translation.BrokenProvider"

        product.status = ProductStatus.PUBLISHED
        product.save()

        product.refresh_from_db()
        assert product.slug == "engagement-ring"

    def test_publishing_without_engine_is_rejected(self, settings):
        """Publikacja bez silnika tłumaczeń jest odrzucana."""
        product = ProductFactory(name="Pierścionek")
        settings.TRANSLATION_PROVIDER = "tests.shared.translation.BrokenProvider"

        product.status = ProductStatus.PUBLISHED
        with pytest.raises(ValidationError) as error:
            product.save()

        assert "slug" in error.value.message_dict

    def test_slug_is_locked_after_publishing(self):
        """Po publikacji slug jest zablokowany."""
        product = PublishedProductFactory(name="Gold ring")

        product.slug = "golden-ring"
        with pytest.raises(ValidationError) as error:
            product.save()

        assert "slug" in error.value.message_dict

    def test_publishing_itself_does_not_block_save(self):
        """Publikacja sama w sobie nie blokuje zapisu."""
        product = ProductFactory(name="Gold ring")

        product.status = ProductStatus.PUBLISHED
        product.save()

        product.refresh_from_db()
        assert product.is_published


@pytest.mark.django_db
class TestProductCategory:
    """Produkt należy do kategorii-liścia (`CONTEXT.md`, Category)."""

    def test_category_without_children_is_allowed(self):
        """Kategoria bez podkategorii jest dozwolona."""
        leaf = CategoryFactory(name="Pierścionki")
        product = ProductFactory.build(category=leaf)

        product.full_clean(exclude=["slug"])

    def test_category_with_children_is_rejected(self):
        """Kategoria z podkategoriami jest odrzucana."""
        root = CategoryFactory(name="Biżuteria")
        CategoryFactory(name="Pierścionki", parent=root)
        product = ProductFactory.build(category=root)

        with pytest.raises(ValidationError) as error:
            product.full_clean(exclude=["slug"])

        assert "category" in error.value.message_dict

    def test_category_with_products_is_not_deleted_silently(self):
        """Kategoria z produktami nie znika po cichu."""
        from django.db.models import ProtectedError

        category = CategoryFactory(name="Pierścionki")
        ProductFactory(category=category)

        with pytest.raises(ProtectedError):
            category.delete()


@pytest.mark.django_db
class TestMadeToOrder:
    """Produkt na zamówienie ma czas realizacji; magazynowy go nie ma (ADR 0024)."""

    def test_made_to_order_product_has_lead_time(self):
        """Produkt na zamówienie ma czas realizacji."""
        product = MadeToOrderProductFactory()

        assert product.is_made_to_order
        assert product.production_time_days == 21

    def test_made_to_order_without_lead_time_is_rejected(self):
        """Brak czasu realizacji przy produkcie na zamówienie jest odrzucany."""
        with pytest.raises(ValidationError) as error:
            ProductFactory(is_made_to_order=True, production_time_days=None)

        assert "production_time_days" in error.value.message_dict

    def test_lead_time_on_stocked_product_is_rejected(self):
        """Czas realizacji przy produkcie magazynowym jest odrzucany."""
        with pytest.raises(ValidationError) as error:
            ProductFactory(is_made_to_order=False, production_time_days=14)

        assert "production_time_days" in error.value.message_dict

    def test_database_rejects_inconsistency_too(self):
        """Baza też nie przepuści niespójności."""
        category = CategoryFactory()

        with pytest.raises(IntegrityError):
            Product.objects.bulk_create(
                [
                    Product(
                        name="Obrączki",
                        slug="wedding-bands",
                        category=category,
                        material="gold",
                        fineness="585",
                        is_made_to_order=True,
                        production_time_days=None,
                    )
                ]
            )


@pytest.mark.django_db
class TestEngraving:
    """Grawer jest flagą na produkcie z osobną ceną (ADR 0018); jedno bez
    drugiego nie ma sensu — flaga bez ceny nie da się wycenić, cena bez flagi
    nie da się kupić."""

    def test_engravable_product_has_engraving_price(self):
        """Produkt grawerowalny ma cenę grawerunku."""
        product = EngravableProductFactory()

        assert product.is_engravable
        assert product.engraving_price_money == Money(4900, "PLN")

    def test_non_engravable_product_has_no_price(self):
        """Produkt bez grawerunku nie ma ceny grawerunku."""
        product = ProductFactory()

        assert not product.is_engravable
        assert product.engraving_price_money is None

    def test_flag_without_price_is_rejected(self):
        """Flaga bez ceny jest odrzucana."""
        with pytest.raises(ValidationError) as error:
            ProductFactory(is_engravable=True, engraving_price=None)

        assert "engraving_price" in error.value.message_dict

    def test_price_without_flag_is_rejected(self):
        """Cena bez flagi jest odrzucana."""
        with pytest.raises(ValidationError) as error:
            ProductFactory(is_engravable=False, engraving_price=4900)

        assert "engraving_price" in error.value.message_dict

    def test_negative_engraving_price_is_rejected(self):
        """Ujemna cena grawerunku jest odrzucana."""
        category = CategoryFactory()

        with pytest.raises(IntegrityError):
            Product.objects.bulk_create(
                [
                    Product(
                        name="Sygnet",
                        category=category,
                        material="gold",
                        fineness="585",
                        is_engravable=True,
                        engraving_price=-1,
                    )
                ]
            )

    def test_database_rejects_inconsistency_too(self):
        """Baza też nie przepuści niespójności."""
        category = CategoryFactory()

        with pytest.raises(IntegrityError):
            Product.objects.bulk_create(
                [
                    Product(
                        name="Sygnet",
                        category=category,
                        material="gold",
                        fineness="585",
                        is_engravable=False,
                        engraving_price=4900,
                    )
                ]
            )


@pytest.mark.django_db
class TestVariantPrice:
    """Cena jest w kolumnie; ręczna ma pierwszeństwo (ADR 0009, ADR 0022)."""

    def test_price_is_money(self):
        """Cena jest pieniędzmi."""
        variant = ProductVariantFactory(price=129900)

        assert variant.price_money == Money(129900, "PLN")
        assert variant.effective_price == Money(129900, "PLN")

    def test_manual_price_takes_precedence(self):
        """Cena ręczna ma pierwszeństwo."""
        variant = ProductVariantFactory(price=129900, manual_price=99900)

        assert variant.price_money == Money(129900, "PLN")
        assert variant.effective_price == Money(99900, "PLN")

    def test_effective_price_is_computed_in_database(self):
        """Adnotacja, bo po tej wartości idzie sortowanie i wybór najtańszego."""
        ProductVariantFactory(price=129900, manual_price=99900)

        variant = ProductVariant.objects.with_effective_price().get()

        assert getattr(variant, EFFECTIVE_PRICE) == 99900
        assert variant.effective_price == Money(99900, "PLN")

    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("price", -1),
            ("manual_price", -1),
            ("metal_weight_grams", Decimal("0.000")),
        ],
    )
    def test_database_rejects_nonsense_value(self, field: str, value: Any):
        """Walidatory pól działają tylko w `full_clean()` — zapis programowy
        (import, `bulk_create`, przeliczenie ceny) omija je."""
        product = PublishedProductFactory()
        fields: dict[str, Any] = {
            "product": product,
            "sku": "BULK-NEG",
            "metal_color": "yellow",
            "metal_weight_grams": Decimal("1.000"),
            "price": 1000,
            "currency": "PLN",
            "vat_rate": Decimal("0.2300"),
            "is_vat_exempt": False,
            "vat_exemption_basis": "",
        }
        fields[field] = value

        with pytest.raises(IntegrityError):
            ProductVariant.objects.bulk_create([ProductVariant(**fields)])

    def test_sku_is_unique_across_catalog(self):
        """SKU jest unikalne w całym katalogu."""
        ProductVariantFactory(sku="SKU-1")

        with pytest.raises(IntegrityError):
            ProductVariantFactory(sku="SKU-1")


@pytest.mark.django_db
class TestVariantVat:
    """Stawka jest przy wariancie; zwolnienie to osobna flaga (ADR 0013)."""

    def test_variant_has_own_rate(self):
        """Wariant ma własną stawkę."""
        variant = ProductVariantFactory(vat_rate=Decimal("0.2300"))

        assert variant.vat_rate == Decimal("0.2300")
        assert not variant.is_vat_exempt

    def test_two_variants_of_one_product_can_differ(self):
        """Dwa warianty jednego produktu mogą mieć różne traktowanie."""
        product = PublishedProductFactory()
        jewellery = ProductVariantFactory(product=product, sku="JEW-1")
        bullion = ProductVariantFactory(vat_exempt=True, product=product, sku="BUL-1")

        assert jewellery.vat_rate == Decimal("0.2300")
        assert bullion.vat_rate is None
        assert bullion.is_vat_exempt

    def test_exemption_requires_legal_basis(self):
        """Zwolnienie wymaga podstawy prawnej."""
        with pytest.raises(ValidationError) as error:
            ProductVariantFactory(
                vat_rate=None, is_vat_exempt=True, vat_exemption_basis=""
            )

        assert "vat_exemption_basis" in error.value.message_dict

    def test_exemption_is_not_zero_rate(self):
        """Zwolnienie nie jest stawką zerową."""
        with pytest.raises(ValidationError) as error:
            ProductVariantFactory(
                vat_rate=Decimal("0.0000"),
                is_vat_exempt=True,
                vat_exemption_basis="art. 122",
            )

        assert "vat_rate" in error.value.message_dict

    def test_variant_without_exemption_needs_rate(self):
        """Wariant bez zwolnienia musi mieć stawkę."""
        with pytest.raises(ValidationError) as error:
            ProductVariantFactory(vat_rate=None, is_vat_exempt=False)

        assert "vat_rate" in error.value.message_dict

    def test_exemption_basis_without_exemption_is_contradiction(self):
        """Podstawa zwolnienia bez zwolnienia jest sprzecznością."""
        with pytest.raises(ValidationError) as error:
            ProductVariantFactory(is_vat_exempt=False, vat_exemption_basis="art. 122")

        assert "vat_exemption_basis" in error.value.message_dict

    def test_database_also_guards_exemption(self):
        """Baza też pilnuje zwolnienia."""
        product = PublishedProductFactory()

        with pytest.raises(IntegrityError):
            ProductVariant.objects.bulk_create(
                [
                    ProductVariant(
                        product=product,
                        sku="BULK-1",
                        metal_color="yellow",
                        metal_weight_grams=Decimal("1.000"),
                        price=1000,
                        currency="PLN",
                        vat_rate=Decimal("0.2300"),
                        is_vat_exempt=True,
                        vat_exemption_basis="art. 122",
                    )
                ]
            )
