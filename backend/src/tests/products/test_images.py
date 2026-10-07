"""Zdjęcia produktu: kadr, trzy rozmiary WebP, widoczność w API."""

from __future__ import annotations

from io import BytesIO
from typing import Any

import pytest
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db.utils import IntegrityError
from django.urls import reverse
from PIL import Image

from apps.products.images import apply_crop, rendition_key, scale_to_width
from apps.products.models import (
    RENDITION_WIDTHS,
    ImageStatus,
    ProductImage,
)
from apps.products.models.image import MAX_ORIGINAL_BYTES, validate_original_size
from core.storage.storages import ProductStorage
from tests.factories.products import ProductVariantFactory, PublishedProductFactory


def make_png(width: int = 2000, height: int = 1000) -> ContentFile:
    """Mała fixture: jednolity prostokąt, tani do zapisania i do policzenia."""
    buffer = BytesIO()
    Image.new("RGB", (width, height), (200, 170, 90)).save(buffer, format="PNG")
    return ContentFile(buffer.getvalue(), name="original.png")


def add_image(product=None, on_commit=None, **kwargs) -> ProductImage:
    """Dodaje zdjęcie produktu z podanym kadrem."""
    product = product or PublishedProductFactory()
    image = ProductImage(product=product, original=make_png(), **kwargs)
    if on_commit is None:
        image.save()
    else:
        with on_commit(execute=True):
            image.save()
    image.refresh_from_db()
    return image


def read_rendition(image: ProductImage, width: int) -> Image.Image:
    """Czyta zapisany rozmiar zdjęcia jako obraz."""
    storage = ProductStorage()
    with storage.open(image.renditions[str(width)], "rb") as handle:
        rendition = Image.open(handle)
        rendition.load()
    return rendition


@pytest.fixture
def on_commit(django_capture_on_commit_callbacks):
    """Uruchamia zadanie odłożone na po zatwierdzeniu transakcji."""
    return django_capture_on_commit_callbacks


@pytest.mark.django_db
class TestCropValidation:
    """Kadr przychodzi z klienta, więc jest sprawdzany."""

    def test_empty_crop_is_allowed(self):
        """Pusty kadr jest dozwolony."""
        image = ProductImage(
            product=PublishedProductFactory(), original=make_png(), crop=None
        )

        image.save()

        assert image.crop is None

    @pytest.mark.parametrize(
        "crop",
        [
            {"x": 0, "y": 0},
            {"x": 0, "y": 0, "width": 10, "height": 10, "extra": 1},
            {"x": -1, "y": 0, "width": 10, "height": 10},
            {"x": 0, "y": 0, "width": 0, "height": 10},
            {"x": 0, "y": 0, "width": "10", "height": 10},
            "nie-slownik",
        ],
    )
    def test_invalid_crop_is_rejected(self, crop: Any):
        """Niepoprawny kadr jest odrzucany."""
        image = ProductImage(
            product=PublishedProductFactory(), original=make_png(), crop=crop
        )

        with pytest.raises(ValidationError) as error:
            image.save()

        assert "crop" in error.value.message_dict


@pytest.mark.django_db
class TestOriginalLimit:
    """Oryginał ma limit dziesięciu megabajtów."""

    def test_limit_is_ten_megabytes(self):
        """Limit to dziesięć megabajtów."""
        assert MAX_ORIGINAL_BYTES == 10 * 1024 * 1024

    def test_file_above_limit_is_rejected(self):
        """Plik ponad limit jest odrzucany."""
        oversized = ContentFile(b"x" * (MAX_ORIGINAL_BYTES + 1), name="big.png")

        with pytest.raises(ValidationError):
            validate_original_size(oversized)

    def test_file_within_limit_passes(self):
        """Plik w limicie przechodzi."""
        validate_original_size(ContentFile(b"x" * 1024, name="small.png"))


class TestGeometry:
    """Kadr i skalowanie liczone bez bazy."""

    def test_crop_cuts_rectangle(self):
        """Kadr wycina prostokąt."""
        source = Image.new("RGB", (100, 100))

        cropped = apply_crop(source, {"x": 10, "y": 20, "width": 30, "height": 40})

        assert cropped.size == (30, 40)

    def test_crop_outside_image_is_clamped(self):
        """Kadr przychodzi z klienta — nie ma powodu ufać, że się mieści."""
        source = Image.new("RGB", (100, 100))

        cropped = apply_crop(source, {"x": 90, "y": 90, "width": 50, "height": 50})

        assert cropped.size == (10, 10)

    def test_empty_crop_keeps_whole_image(self):
        """Pusty kadr zostawia całe zdjęcie."""
        source = Image.new("RGB", (100, 100))

        assert apply_crop(source, None).size == (100, 100)

    def test_scaling_keeps_aspect_ratio(self):
        """Skalowanie zachowuje proporcje."""
        source = Image.new("RGB", (2000, 1000))

        assert scale_to_width(source, 400).size == (400, 200)

    def test_image_narrower_than_size_is_not_upscaled(self):
        """Powiększanie nie dokłada szczegółu, a waży swoje."""
        source = Image.new("RGB", (300, 150))

        assert scale_to_width(source, 1600).size == (300, 150)


@pytest.mark.django_db
class TestRendering:
    """Zadanie tnie oryginał i zapisuje trzy rozmiary WebP."""

    def test_three_sizes_are_created(self, on_commit):
        """Powstają trzy rozmiary."""
        image = add_image(on_commit=on_commit)

        assert sorted(image.renditions) == sorted(
            str(width) for width in RENDITION_WIDTHS
        )

    def test_sizes_are_400_800_1600(self):
        """Rozmiary to 400, 800 i 1600."""
        assert RENDITION_WIDTHS == (400, 800, 1600)

    def test_image_is_ready_after_task(self, on_commit):
        """Zdjęcie jest gotowe po zadaniu."""
        image = add_image(on_commit=on_commit)

        assert image.status == ImageStatus.READY

    def test_image_is_processing_before_task(self):
        """Przed zadaniem zdjęcie jest w przetwarzaniu."""
        image = add_image()

        assert image.status == ImageStatus.PROCESSING
        assert image.renditions == {}

    def test_files_are_webp(self, on_commit):
        """Pliki są w formacie WebP."""
        image = add_image(on_commit=on_commit)

        assert read_rendition(image, 800).format == "WEBP"

    def test_widths_match_size(self, on_commit):
        """Szerokości są zgodne z rozmiarem."""
        image = add_image(on_commit=on_commit)

        assert read_rendition(image, 400).width == 400
        assert read_rendition(image, 800).width == 800
        assert read_rendition(image, 1600).width == 1600

    def test_crop_changes_result_aspect_ratio(self, on_commit):
        """Kadr zmienia proporcje wyniku."""
        image = add_image(
            on_commit=on_commit, crop={"x": 0, "y": 0, "width": 1000, "height": 1000}
        )

        rendition = read_rendition(image, 400)

        assert rendition.size == (400, 400)

    def test_key_has_fixed_shape(self, on_commit):
        """Klucz ma ustalony kształt."""
        image = add_image(on_commit=on_commit)

        key = image.renditions["400"]

        assert key.startswith(f"products/{image.pk}/")
        assert key.endswith("-400.webp")

    def test_key_has_no_host_or_bucket(self, on_commit):
        """Klucz nie zawiera hosta ani bucketa."""
        image = add_image(on_commit=on_commit)

        key = image.renditions["800"]

        assert "http" not in key
        assert not key.startswith("originals/")

    def test_key_shape_is_computable(self):
        """Kształt klucza jest wyliczalny."""
        image = ProductImage()
        image.pk = "abc"  # type: ignore[bad-assignment]

        assert rendition_key(image, "token", 400) == "products/abc/token-400.webp"


@pytest.mark.django_db
class TestRecrop:
    """Zmiana kadru uruchamia to samo zadanie na zachowanym oryginale."""

    def test_crop_change_rerenders_image(self, on_commit):
        """Zmiana kadru przelicza zdjęcie."""
        image = add_image(on_commit=on_commit)
        first = image.renditions["400"]

        image.crop = {"x": 0, "y": 0, "width": 500, "height": 500}
        with on_commit(execute=True):
            image.save()
        image.refresh_from_db()

        assert image.renditions["400"] != first
        assert image.status == ImageStatus.READY

    def test_crop_change_needs_no_reupload(self, on_commit):
        """Zmiana kadru nie wymaga ponownego wgrania."""
        image = add_image(on_commit=on_commit)
        original_key = image.original_key

        image.crop = {"x": 0, "y": 0, "width": 500, "height": 500}
        with on_commit(execute=True):
            image.save()
        image.refresh_from_db()

        assert image.original_key == original_key

    def test_new_crop_is_visible_in_result(self, on_commit):
        """Nowy kadr widać w wyniku."""
        image = add_image(on_commit=on_commit)

        image.crop = {"x": 0, "y": 0, "width": 400, "height": 200}
        with on_commit(execute=True):
            image.save()
        image.refresh_from_db()

        assert read_rendition(image, 400).size == (400, 200)

    def test_save_without_crop_change_does_not_rerender(self, on_commit):
        """Zapis bez zmiany kadru nie przelicza zdjęcia."""
        image = add_image(on_commit=on_commit)
        first = image.renditions["400"]

        with on_commit(execute=True):
            image.alt_text = "Złoty pierścionek"
            image.save()
        image.refresh_from_db()

        assert image.renditions["400"] == first


@pytest.mark.django_db
class TestGalleryRules:
    """Kolejność, zdjęcie główne i przypisanie do wariantu."""

    def test_order_follows_position(self, on_commit):
        """Kolejność idzie po `position`."""
        product = PublishedProductFactory()
        add_image(product=product, on_commit=on_commit, position=2, alt_text="druga")
        add_image(product=product, on_commit=on_commit, position=1, alt_text="pierwsza")

        gallery = product.images.all()  # type: ignore[missing-attribute]
        assert [image.alt_text for image in gallery] == [
            "pierwsza",
            "druga",
        ]

    def test_one_main_image_per_product(self, on_commit):
        """Zdjęcie główne jest jedno na produkt."""
        product = PublishedProductFactory()
        add_image(product=product, on_commit=on_commit, is_primary=True)

        with pytest.raises(IntegrityError):
            add_image(product=product, on_commit=on_commit, is_primary=True)

    def test_two_products_can_have_own_main_image(self, on_commit):
        """Dwa produkty mogą mieć swoje zdjęcia główne."""
        first = add_image(on_commit=on_commit, is_primary=True)
        second = add_image(on_commit=on_commit, is_primary=True)

        assert first.is_primary and second.is_primary

    def test_image_can_belong_to_variant(self, on_commit):
        """Zdjęcie może należeć do wariantu."""
        product = PublishedProductFactory()
        variant = ProductVariantFactory(product=product)

        image = add_image(product=product, on_commit=on_commit, variant=variant)

        assert image.variant == variant

    def test_variant_from_other_product_is_rejected(self):
        """Wariant z innego produktu jest odrzucany."""
        product = PublishedProductFactory()
        other_variant = ProductVariantFactory()
        image = ProductImage(
            product=product, original=make_png(), variant=other_variant
        )

        with pytest.raises(ValidationError) as error:
            image.full_clean(exclude=["original"])

        assert "variant" in error.value.message_dict


@pytest.mark.django_db
class TestImagesInApi:
    """API produktu i wariantu zwraca adresy per rozmiar."""

    def _detail(self, api_client, slug: str | None) -> dict[str, Any]:
        response: Any = api_client.get(reverse("product-detail", kwargs={"slug": slug}))
        assert response.status_code == 200, response.content
        return response.json()

    def test_product_returns_gallery_with_urls(self, api_client, on_commit):
        """Produkt zwraca galerię z adresami."""
        product = PublishedProductFactory()
        add_image(product=product, on_commit=on_commit, alt_text="Pierścionek")

        body = self._detail(api_client, product.slug)

        assert len(body["images"]) == 1
        assert sorted(body["images"][0]["urls"]) == ["1600", "400", "800"]
        assert body["images"][0]["altText"] == "Pierścionek"

    def test_urls_point_to_public_bucket_without_signature(self, api_client, on_commit):
        """Adresy wskazują bucket publiczny bez podpisu."""
        product = PublishedProductFactory()
        add_image(product=product, on_commit=on_commit)

        body = self._detail(api_client, product.slug)
        url = body["images"][0]["urls"]["800"]

        assert "X-Amz-Signature" not in url
        assert url.endswith("-800.webp")

    def test_processing_image_is_skipped(self, api_client):
        """Zdjęcie w przetwarzaniu jest pomijane."""
        product = PublishedProductFactory()
        add_image(product=product)

        body = self._detail(api_client, product.slug)

        assert body["images"] == []

    def test_variant_returns_its_images(self, api_client, on_commit):
        """Wariant zwraca swoje zdjęcia."""
        product = PublishedProductFactory()
        variant = ProductVariantFactory(product=product)
        add_image(product=product, on_commit=on_commit, variant=variant)

        body = self._detail(api_client, product.slug)

        assert len(body["variants"][0]["images"]) == 1

    def test_product_image_is_not_in_variant(self, api_client, on_commit):
        """Zdjęcie produktu nie wchodzi do wariantu."""
        product = PublishedProductFactory()
        ProductVariantFactory(product=product)
        add_image(product=product, on_commit=on_commit)

        body = self._detail(api_client, product.slug)

        assert body["variants"][0]["images"] == []
        assert len(body["images"]) == 1

    def test_gallery_does_not_multiply_queries(
        self, api_client, on_commit, django_assert_max_num_queries
    ):
        """Galeria trzech zdjęć nie dokłada zapytań na każde zdjęcie.

        Pierwsze żądanie rozgrzewa procesowy cache `ContentType` — bez tego
        wynik zależał od kolejności testów (siódme zapytanie o typ treści
        pojawiało się tylko, gdy nikt wcześniej go nie zapisał).
        """
        product = PublishedProductFactory()
        for position in range(3):
            add_image(product=product, on_commit=on_commit, position=position)
        url = reverse("product-detail", kwargs={"slug": product.slug})
        api_client.get(url)

        with django_assert_max_num_queries(6):
            api_client.get(url)
