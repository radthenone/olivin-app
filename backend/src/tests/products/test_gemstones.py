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
    """Mały plik PDF certyfikatu."""
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

    def test_variant_without_stones_is_valid(self):
        """Wariant bez kamieni jest poprawny."""
        variant = ProductVariantFactory()

        assert variant.gemstones.count() == 0  # type: ignore[missing-attribute]

    def test_variant_can_have_many_stones(self):
        """Wariant może mieć wiele kamieni."""
        variant = ProductVariantFactory()
        GemstoneFactory(variant=variant, kind=Stone.DIAMOND, carat=Decimal("0.500"))
        GemstoneFactory(variant=variant, kind=Stone.SAPPHIRE, carat=Decimal("0.250"))

        assert variant.gemstones.count() == 2  # type: ignore[missing-attribute]

    def test_stones_are_ordered_from_largest(self):
        """Kamienie idą od największego."""
        variant = ProductVariantFactory()
        GemstoneFactory(variant=variant, carat=Decimal("0.250"))
        GemstoneFactory(variant=variant, carat=Decimal("1.000"))

        carats = [stone.carat for stone in variant.gemstones.all()]  # type: ignore[missing-attribute]

        assert carats == [Decimal("1.000"), Decimal("0.250")]

    def test_descriptive_parameters_are_optional(self):
        """Parametry opisowe są opcjonalne."""
        stone = GemstoneFactory(clarity="", colour="", cut="")

        stone.full_clean()
        assert stone.clarity == ""

    def test_weight_must_be_positive(self):
        """Masa musi być dodatnia."""
        variant = ProductVariantFactory()

        with pytest.raises(IntegrityError):
            Gemstone.objects.bulk_create(
                [Gemstone(variant=variant, kind=Stone.DIAMOND, carat=Decimal("0.000"))]
            )

    def test_deleting_variant_deletes_stones(self):
        """Skasowanie wariantu zabiera kamienie."""
        variant = ProductVariantFactory()
        GemstoneFactory(variant=variant)

        variant.delete()

        assert Gemstone.objects.count() == 0


@pytest.mark.django_db
class TestCertificateValidation:
    """Certyfikat jest dokumentem PDF o rozsądnym rozmiarze."""

    def test_pdf_file_passes(self):
        """Plik PDF przechodzi."""
        validate_certificate(certificate_file())

    def test_other_format_is_rejected(self):
        """Inny format jest odrzucany."""
        with pytest.raises(ValidationError):
            validate_certificate(certificate_file(name="skan.png"))

    def test_file_above_limit_is_rejected(self):
        """Plik ponad limit jest odrzucany."""
        oversized = ContentFile(b"x" * (MAX_CERTIFICATE_BYTES + 1), name="duzy.pdf")

        with pytest.raises(ValidationError):
            validate_certificate(oversized)

    def test_certificate_without_lab_and_number_is_rejected(self):
        """Dokumentu, którego nie da się z niczym zestawić, nie ma po co
        pokazywać klientowi."""
        stone = GemstoneFactory(laboratory="", certificate_number="")
        stone.certificate = certificate_file()

        with pytest.raises(ValidationError) as error:
            stone.full_clean()

        assert "laboratory" in error.value.message_dict

    def test_number_alone_is_enough(self):
        """Sam numer certyfikatu wystarczy."""
        stone = GemstoneFactory(laboratory="", certificate_number="2141234567")
        stone.certificate = certificate_file()

        stone.full_clean()

    def test_stone_without_certificate_needs_no_lab(self):
        """Kamień bez certyfikatu nie wymaga laboratorium."""
        GemstoneFactory(laboratory="", certificate_number="").full_clean()


@pytest.mark.django_db
class TestGemstonesInApi:
    """API wariantu zwraca kamienie z parametrami i adresem certyfikatu."""

    def test_stones_are_exposed_with_parameters(self, api_client):
        """Kamienie wychodzą z parametrami."""
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

    def test_many_stones_are_exposed_as_list(self, api_client):
        """Wiele kamieni wychodzi listą."""
        product = PublishedProductFactory()
        variant = ProductVariantFactory(product=product)
        GemstoneFactory(variant=variant, carat=Decimal("1.000"))
        GemstoneFactory(variant=variant, carat=Decimal("0.250"))

        assert len(_variant_body(api_client, product)["gemstones"]) == 2

    def test_variant_without_stones_has_empty_list(self, api_client):
        """Wariant bez kamieni ma pustą listę."""
        product = PublishedProductFactory()
        ProductVariantFactory(product=product)

        assert _variant_body(api_client, product)["gemstones"] == []

    def test_missing_certificate_gives_empty_url(self, api_client):
        """Brak certyfikatu daje pusty adres."""
        product = PublishedProductFactory()
        variant = ProductVariantFactory(product=product)
        GemstoneFactory(variant=variant)

        stone = _variant_body(api_client, product)["gemstones"][0]

        assert stone["certificateUrl"] is None

    def test_certificate_gives_signed_url(self, api_client):
        """Certyfikat daje adres podpisany."""
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

    def test_certificate_url_has_expiry(self, api_client):
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

    def test_url_is_not_permanent_bucket_link(self, api_client):
        """Adres nie jest stałym odnośnikiem do bucketa."""
        product = PublishedProductFactory()
        variant = ProductVariantFactory(product=product)
        GemstoneFactory(
            variant=variant,
            laboratory="GIA",
            certificate=certificate_file(),
        )

        url = _variant_body(api_client, product)["gemstones"][0]["certificateUrl"]

        assert "?" in url

    def test_stones_do_not_multiply_queries(
        self, api_client, django_assert_max_num_queries
    ):
        """Kamienie nie mnożą zapytań."""
        product = PublishedProductFactory()
        for index in range(3):
            variant = ProductVariantFactory(product=product, sku=f"V-{index}")
            GemstoneFactory(variant=variant)

        with django_assert_max_num_queries(7):
            api_client.get(reverse("product-detail", kwargs={"slug": product.slug}))
