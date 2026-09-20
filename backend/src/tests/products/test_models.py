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
    MadeToOrderProductFactory,
    ProductFactory,
    ProductVariantFactory,
    PublishedProductFactory,
)


@pytest.mark.django_db
class TestProductSlug:
    """Slug produktu zamraża się przy publikacji, nie przy pierwszym zapisie."""

    def test_szkic_nie_ma_jeszcze_adresu(self):
        """Adres powstaje przy publikacji (`.ai/project.md`) — szkic nie ma
        go pod czym wyświetlić, a angielska nazwa nie musi jeszcze istnieć."""
        product = ProductFactory(name="Pierścionek")

        assert product.slug is None

    def test_wiele_szkicow_wspolistnieje_bez_adresow(self):
        """Kolumna sluga jest unikalna, więc pusty adres musi być `NULL`,
        a nie pustym łańcuchem — dwa puste łańcuchy by się zderzyły."""
        first = ProductFactory(name="Pierwszy")
        second = ProductFactory(name="Drugi")

        assert first.slug is None
        assert second.slug is None
        assert Product.objects.filter(slug__isnull=True).count() == 2

    def test_publikacja_nadaje_adres_z_angielskiego_brzmienia(self):
        product = PublishedProductFactory(name="Pierścionek")

        assert product.slug == "en-pierscionek"

    def test_nazwa_polska_nie_wchodzi_do_adresu_wprost(self):
        product = PublishedProductFactory(name="Łańcuszek złoty")

        assert product.slug != "lancuszek-zloty"

    def test_kolizja_dostaje_przyrostek(self):
        PublishedProductFactory(name="Ring")
        second = PublishedProductFactory(name="Ring")

        assert second.slug == "en-ring-2"

    def test_szkic_wolno_jeszcze_poprawic(self):
        product = ProductFactory(name="Gold ring", slug="gold-ring")

        product.slug = "golden-ring"
        product.save()

        product.refresh_from_db()
        assert product.slug == "golden-ring"

    def test_slug_wpisany_recznie_przezywa_publikacje(self, settings):
        """Wpisany adres ma pierwszeństwo i nie rusza silnika — to jedyna
        droga działająca bez sieci."""
        product = ProductFactory(name="Pierścionek", slug="engagement-ring")
        settings.TRANSLATION_PROVIDER = "tests.shared.translation.BrokenProvider"

        product.status = ProductStatus.PUBLISHED
        product.save()

        product.refresh_from_db()
        assert product.slug == "engagement-ring"

    def test_publikacja_bez_silnika_jest_odrzucona(self, settings):
        product = ProductFactory(name="Pierścionek")
        settings.TRANSLATION_PROVIDER = "tests.shared.translation.BrokenProvider"

        product.status = ProductStatus.PUBLISHED
        with pytest.raises(ValidationError) as error:
            product.save()

        assert "slug" in error.value.message_dict

    def test_po_publikacji_slug_jest_zablokowany(self):
        product = PublishedProductFactory(name="Gold ring")

        product.slug = "golden-ring"
        with pytest.raises(ValidationError) as error:
            product.save()

        assert "slug" in error.value.message_dict

    def test_publikacja_sama_w_sobie_nie_blokuje_zapisu(self):
        product = ProductFactory(name="Gold ring")

        product.status = ProductStatus.PUBLISHED
        product.save()

        product.refresh_from_db()
        assert product.is_published


@pytest.mark.django_db
class TestProductCategory:
    """Produkt należy do kategorii-liścia (`CONTEXT.md`, Category)."""

    def test_kategoria_bez_podkategorii_jest_dozwolona(self):
        leaf = CategoryFactory(name="Pierścionki")
        product = ProductFactory.build(category=leaf)

        product.full_clean(exclude=["slug"])

    def test_kategoria_z_podkategoriami_jest_odrzucona(self):
        root = CategoryFactory(name="Biżuteria")
        CategoryFactory(name="Pierścionki", parent=root)
        product = ProductFactory.build(category=root)

        with pytest.raises(ValidationError) as error:
            product.full_clean(exclude=["slug"])

        assert "category" in error.value.message_dict

    def test_kategoria_z_produktami_nie_znika_po_cichu(self):
        from django.db.models import ProtectedError

        category = CategoryFactory(name="Pierścionki")
        ProductFactory(category=category)

        with pytest.raises(ProtectedError):
            category.delete()


@pytest.mark.django_db
class TestMadeToOrder:
    """Produkt na zamówienie ma czas realizacji; magazynowy go nie ma (ADR 0024)."""

    def test_produkt_na_zamowienie_ma_czas_realizacji(self):
        product = MadeToOrderProductFactory()

        assert product.is_made_to_order
        assert product.production_time_days == 21

    def test_brak_czasu_realizacji_przy_produkcie_na_zamowienie_jest_odrzucony(self):
        with pytest.raises(ValidationError) as error:
            ProductFactory(is_made_to_order=True, production_time_days=None)

        assert "production_time_days" in error.value.message_dict

    def test_czas_realizacji_przy_produkcie_magazynowym_jest_odrzucony(self):
        with pytest.raises(ValidationError) as error:
            ProductFactory(is_made_to_order=False, production_time_days=14)

        assert "production_time_days" in error.value.message_dict

    def test_baza_tez_nie_przepusci_niespojnosci(self):
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
class TestVariantPrice:
    """Cena jest w kolumnie; ręczna ma pierwszeństwo (ADR 0009, ADR 0022)."""

    def test_cena_jest_pieniedzmi(self):
        variant = ProductVariantFactory(price=129900)

        assert variant.price_money == Money(129900, "PLN")
        assert variant.effective_price == Money(129900, "PLN")

    def test_cena_reczna_ma_pierwszenstwo(self):
        variant = ProductVariantFactory(price=129900, manual_price=99900)

        assert variant.price_money == Money(129900, "PLN")
        assert variant.effective_price == Money(99900, "PLN")

    def test_cena_skuteczna_liczy_sie_takze_w_bazie(self):
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
    def test_baza_nie_przepusci_bezsensownej_wartosci(self, field: str, value: Any):
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

    def test_sku_jest_unikalne_w_calym_katalogu(self):
        ProductVariantFactory(sku="SKU-1")

        with pytest.raises(IntegrityError):
            ProductVariantFactory(sku="SKU-1")


@pytest.mark.django_db
class TestVariantVat:
    """Stawka jest przy wariancie; zwolnienie to osobna flaga (ADR 0013)."""

    def test_wariant_ma_wlasna_stawke(self):
        variant = ProductVariantFactory(vat_rate=Decimal("0.2300"))

        assert variant.vat_rate == Decimal("0.2300")
        assert not variant.is_vat_exempt

    def test_dwa_warianty_jednego_produktu_moga_miec_rozne_traktowanie(self):
        product = PublishedProductFactory()
        jewellery = ProductVariantFactory(product=product, sku="JEW-1")
        bullion = ProductVariantFactory(vat_exempt=True, product=product, sku="BUL-1")

        assert jewellery.vat_rate == Decimal("0.2300")
        assert bullion.vat_rate is None
        assert bullion.is_vat_exempt

    def test_zwolnienie_wymaga_podstawy_prawnej(self):
        with pytest.raises(ValidationError) as error:
            ProductVariantFactory(
                vat_rate=None, is_vat_exempt=True, vat_exemption_basis=""
            )

        assert "vat_exemption_basis" in error.value.message_dict

    def test_zwolnienie_nie_jest_stawka_zerowa(self):
        with pytest.raises(ValidationError) as error:
            ProductVariantFactory(
                vat_rate=Decimal("0.0000"),
                is_vat_exempt=True,
                vat_exemption_basis="art. 122",
            )

        assert "vat_rate" in error.value.message_dict

    def test_wariant_bez_zwolnienia_musi_miec_stawke(self):
        with pytest.raises(ValidationError) as error:
            ProductVariantFactory(vat_rate=None, is_vat_exempt=False)

        assert "vat_rate" in error.value.message_dict

    def test_podstawa_zwolnienia_bez_zwolnienia_jest_sprzecznoscia(self):
        with pytest.raises(ValidationError) as error:
            ProductVariantFactory(is_vat_exempt=False, vat_exemption_basis="art. 122")

        assert "vat_exemption_basis" in error.value.message_dict

    def test_baza_tez_pilnuje_zwolnienia(self):
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
