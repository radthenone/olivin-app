"""Kamienie na wariancie i certyfikaty laboratorium."""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from urllib.parse import parse_qs, urlparse

import pytest
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db.utils import IntegrityError
from django.urls import reverse

from apps.products.models import Gemstone, Stone
from apps.products.models.gemstone import (
    MAX_CERTIFICATE_BYTES,
    validate_certificate,
)
from tests.factories.products import (
    GemstoneFactory,
    ProductVariantFactory,
    PublishedProductFactory,
)

PDF = b"%PDF-1.4 olivin"


def certificate_file(name: str = "gia.pdf", size: int = len(PDF)) -> ContentFile:
    return ContentFile(PDF.ljust(size, b" "), name=name)


def _variant_body(api_client, product) -> dict[str, Any]:
    response: Any = api_client.get(
        reverse("product-detail", kwargs={"slug": product.slug})
    )
    assert response.status_code == 200, response.content
    return response.json()["variants"][0]


@pytest.mark.django_db
class TestGemstonesOnVariant:
    """Wariant może mieć wiele kamieni albo żadnego."""

    def test_wariant_bez_kamieni_jest_poprawny(self):
        variant = ProductVariantFactory()

        assert variant.gemstones.count() == 0  # type: ignore[missing-attribute]

    def test_wariant_moze_miec_wiele_kamieni(self):
        variant = ProductVariantFactory()
        GemstoneFactory(variant=variant, kind=Stone.DIAMOND, carat=Decimal("0.500"))
        GemstoneFactory(variant=variant, kind=Stone.SAPPHIRE, carat=Decimal("0.250"))

        assert variant.gemstones.count() == 2  # type: ignore[missing-attribute]

    def test_kamienie_ida_od_najwiekszego(self):
        variant = ProductVariantFactory()
        GemstoneFactory(variant=variant, carat=Decimal("0.250"))
        GemstoneFactory(variant=variant, carat=Decimal("1.000"))

        carats = [stone.carat for stone in variant.gemstones.all()]  # type: ignore[missing-attribute]

        assert carats == [Decimal("1.000"), Decimal("0.250")]

    def test_parametry_opisowe_sa_opcjonalne(self):
        stone = GemstoneFactory(clarity="", colour="", cut="")

        stone.full_clean()
        assert stone.clarity == ""

    def test_masa_musi_byc_dodatnia(self):
        variant = ProductVariantFactory()

        with pytest.raises(IntegrityError):
            Gemstone.objects.bulk_create(
                [Gemstone(variant=variant, kind=Stone.DIAMOND, carat=Decimal("0.000"))]
            )

    def test_skasowanie_wariantu_zabiera_kamienie(self):
        variant = ProductVariantFactory()
        GemstoneFactory(variant=variant)

        variant.delete()

        assert Gemstone.objects.count() == 0


@pytest.mark.django_db
class TestCertificateValidation:
    """Certyfikat jest dokumentem PDF o rozsądnym rozmiarze."""

    def test_plik_pdf_przechodzi(self):
        validate_certificate(certificate_file())

    def test_inny_format_jest_odrzucony(self):
        with pytest.raises(ValidationError):
            validate_certificate(certificate_file(name="skan.png"))

    def test_plik_ponad_limit_jest_odrzucony(self):
        oversized = ContentFile(b"x" * (MAX_CERTIFICATE_BYTES + 1), name="duzy.pdf")

        with pytest.raises(ValidationError):
            validate_certificate(oversized)

    def test_certyfikat_bez_laboratorium_i_numeru_jest_odrzucony(self):
        """Dokumentu, którego nie da się z niczym zestawić, nie ma po co
        pokazywać klientowi."""
        stone = GemstoneFactory(laboratory="", certificate_number="")
        stone.certificate = certificate_file()

        with pytest.raises(ValidationError) as error:
            stone.full_clean()

        assert "laboratory" in error.value.message_dict

    def test_sam_numer_wystarczy(self):
        stone = GemstoneFactory(laboratory="", certificate_number="2141234567")
        stone.certificate = certificate_file()

        stone.full_clean()

    def test_kamien_bez_certyfikatu_nie_wymaga_laboratorium(self):
        GemstoneFactory(laboratory="", certificate_number="").full_clean()


@pytest.mark.django_db
class TestGemstonesInApi:
    """API wariantu zwraca kamienie z parametrami i adresem certyfikatu."""

    def test_kamienie_wychodza_z_parametrami(self, api_client):
        product = PublishedProductFactory()
        variant = ProductVariantFactory(product=product)
        GemstoneFactory(
            variant=variant,
            kind=Stone.DIAMOND,
            carat=Decimal("0.750"),
            clarity="VS1",
            colour="G",
            cut="brilliant",
        )

        stone = _variant_body(api_client, product)["gemstones"][0]

        assert stone["kind"] == "diamond"
        assert stone["carat"] == "0.750"
        assert stone["clarity"] == "VS1"
        assert stone["colour"] == "G"
        assert stone["cut"] == "brilliant"

    def test_wiele_kamieni_wychodzi_lista(self, api_client):
        product = PublishedProductFactory()
        variant = ProductVariantFactory(product=product)
        GemstoneFactory(variant=variant, carat=Decimal("1.000"))
        GemstoneFactory(variant=variant, carat=Decimal("0.250"))

        assert len(_variant_body(api_client, product)["gemstones"]) == 2

    def test_wariant_bez_kamieni_ma_pusta_liste(self, api_client):
        product = PublishedProductFactory()
        ProductVariantFactory(product=product)

        assert _variant_body(api_client, product)["gemstones"] == []

    def test_brak_certyfikatu_daje_pusty_adres(self, api_client):
        product = PublishedProductFactory()
        variant = ProductVariantFactory(product=product)
        GemstoneFactory(variant=variant)

        stone = _variant_body(api_client, product)["gemstones"][0]

        assert stone["certificateUrl"] is None

    def test_certyfikat_daje_adres_podpisany(self, api_client):
        product = PublishedProductFactory()
        variant = ProductVariantFactory(product=product)
        GemstoneFactory(
            variant=variant,
            laboratory="GIA",
            certificate_number="2141234567",
            certificate=certificate_file(),
        )

        url = _variant_body(api_client, product)["gemstones"][0]["certificateUrl"]

        assert "X-Amz-Signature" in url

    def test_adres_certyfikatu_ma_czas_waznosci(self, api_client):
        """Prywatny bucket `documents` — odnośnik działa przez ustalony czas,
        a nie na zawsze (ADR 0025)."""
        product = PublishedProductFactory()
        variant = ProductVariantFactory(product=product)
        GemstoneFactory(
            variant=variant,
            laboratory="GIA",
            certificate=certificate_file(),
        )

        url = _variant_body(api_client, product)["gemstones"][0]["certificateUrl"]
        expires = parse_qs(urlparse(url).query).get("X-Amz-Expires", ["0"])[0]

        assert int(expires) > 0

    def test_adres_nie_jest_stalym_odnosnikiem_do_bucketa(self, api_client):
        product = PublishedProductFactory()
        variant = ProductVariantFactory(product=product)
        GemstoneFactory(
            variant=variant,
            laboratory="GIA",
            certificate=certificate_file(),
        )

        url = _variant_body(api_client, product)["gemstones"][0]["certificateUrl"]

        assert "?" in url

    def test_kamienie_nie_mnoza_zapytan(
        self, api_client, django_assert_max_num_queries
    ):
        product = PublishedProductFactory()
        for index in range(3):
            variant = ProductVariantFactory(product=product, sku=f"V-{index}")
            GemstoneFactory(variant=variant)

        with django_assert_max_num_queries(7):
            api_client.get(reverse("product-detail", kwargs={"slug": product.slug}))
