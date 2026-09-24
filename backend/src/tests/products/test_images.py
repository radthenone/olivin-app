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

    def test_pusty_kadr_jest_dozwolony(self):
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
    def test_kadr_niepoprawny_jest_odrzucony(self, crop: Any):
        image = ProductImage(
            product=PublishedProductFactory(), original=make_png(), crop=crop
        )

        with pytest.raises(ValidationError) as error:
            image.save()

        assert "crop" in error.value.message_dict


@pytest.mark.django_db
class TestOriginalLimit:
    """Oryginał ma limit dziesięciu megabajtów."""

    def test_limit_to_dziesiec_megabajtow(self):
        assert MAX_ORIGINAL_BYTES == 10 * 1024 * 1024

    def test_plik_ponad_limit_jest_odrzucony(self):
        oversized = ContentFile(b"x" * (MAX_ORIGINAL_BYTES + 1), name="big.png")

        with pytest.raises(ValidationError):
            validate_original_size(oversized)

    def test_plik_w_limicie_przechodzi(self):
        validate_original_size(ContentFile(b"x" * 1024, name="small.png"))


class TestGeometry:
    """Kadr i skalowanie liczone bez bazy."""

    def test_kadr_wycina_prostokat(self):
        source = Image.new("RGB", (100, 100))

        cropped = apply_crop(source, {"x": 10, "y": 20, "width": 30, "height": 40})

        assert cropped.size == (30, 40)

    def test_kadr_wychodzacy_poza_zdjecie_jest_przyciety(self):
        """Kadr przychodzi z klienta — nie ma powodu ufać, że się mieści."""
        source = Image.new("RGB", (100, 100))

        cropped = apply_crop(source, {"x": 90, "y": 90, "width": 50, "height": 50})

        assert cropped.size == (10, 10)

    def test_pusty_kadr_zostawia_cale_zdjecie(self):
        source = Image.new("RGB", (100, 100))

        assert apply_crop(source, None).size == (100, 100)

    def test_skalowanie_zachowuje_proporcje(self):
        source = Image.new("RGB", (2000, 1000))

        assert scale_to_width(source, 400).size == (400, 200)

    def test_zdjecie_wezsze_niz_rozmiar_nie_jest_powiekszane(self):
        """Powiększanie nie dokłada szczegółu, a waży swoje."""
        source = Image.new("RGB", (300, 150))

        assert scale_to_width(source, 1600).size == (300, 150)


@pytest.mark.django_db
class TestRendering:
    """Zadanie tnie oryginał i zapisuje trzy rozmiary WebP."""

    def test_powstaja_trzy_rozmiary(self, on_commit):
        image = add_image(on_commit=on_commit)

        assert sorted(image.renditions) == sorted(
            str(width) for width in RENDITION_WIDTHS
        )

    def test_rozmiary_to_400_800_1600(self):
        assert RENDITION_WIDTHS == (400, 800, 1600)

    def test_zdjecie_jest_gotowe_po_zadaniu(self, on_commit):
        image = add_image(on_commit=on_commit)

        assert image.status == ImageStatus.READY

    def test_przed_zadaniem_zdjecie_jest_w_przetwarzaniu(self):
        image = add_image()

        assert image.status == ImageStatus.PROCESSING
        assert image.renditions == {}

    def test_pliki_sa_w_formacie_webp(self, on_commit):
        image = add_image(on_commit=on_commit)

        assert read_rendition(image, 800).format == "WEBP"

    def test_szerokosci_sa_zgodne_z_rozmiarem(self, on_commit):
        image = add_image(on_commit=on_commit)

        assert read_rendition(image, 400).width == 400
        assert read_rendition(image, 800).width == 800
        assert read_rendition(image, 1600).width == 1600

    def test_kadr_zmienia_proporcje_wyniku(self, on_commit):
        image = add_image(
            on_commit=on_commit, crop={"x": 0, "y": 0, "width": 1000, "height": 1000}
        )

        rendition = read_rendition(image, 400)

        assert rendition.size == (400, 400)

    def test_klucz_ma_ustalony_ksztalt(self, on_commit):
        image = add_image(on_commit=on_commit)

        key = image.renditions["400"]

        assert key.startswith(f"products/{image.pk}/")
        assert key.endswith("-400.webp")

    def test_klucz_nie_zawiera_hosta_ani_bucketa(self, on_commit):
        image = add_image(on_commit=on_commit)

        key = image.renditions["800"]

        assert "http" not in key
        assert not key.startswith("originals/")

    def test_ksztalt_klucza_jest_wyliczalny(self):
        image = ProductImage()
        image.pk = "abc"  # type: ignore[bad-assignment]

        assert rendition_key(image, "token", 400) == "products/abc/token-400.webp"


@pytest.mark.django_db
class TestRecrop:
    """Zmiana kadru uruchamia to samo zadanie na zachowanym oryginale."""

    def test_zmiana_kadru_przelicza_zdjecie(self, on_commit):
        image = add_image(on_commit=on_commit)
        first = image.renditions["400"]

        image.crop = {"x": 0, "y": 0, "width": 500, "height": 500}
        with on_commit(execute=True):
            image.save()
        image.refresh_from_db()

        assert image.renditions["400"] != first
        assert image.status == ImageStatus.READY

    def test_zmiana_kadru_nie_wymaga_ponownego_wgrania(self, on_commit):
        image = add_image(on_commit=on_commit)
        original_key = image.original_key

        image.crop = {"x": 0, "y": 0, "width": 500, "height": 500}
        with on_commit(execute=True):
            image.save()
        image.refresh_from_db()

        assert image.original_key == original_key

    def test_nowy_kadr_widac_w_wyniku(self, on_commit):
        image = add_image(on_commit=on_commit)

        image.crop = {"x": 0, "y": 0, "width": 400, "height": 200}
        with on_commit(execute=True):
            image.save()
        image.refresh_from_db()

        assert read_rendition(image, 400).size == (400, 200)

    def test_zapis_bez_zmiany_kadru_nie_przelicza(self, on_commit):
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

    def test_kolejnosc_idzie_po_position(self, on_commit):
        product = PublishedProductFactory()
        add_image(product=product, on_commit=on_commit, position=2, alt_text="druga")
        add_image(product=product, on_commit=on_commit, position=1, alt_text="pierwsza")

        gallery = product.images.all()  # type: ignore[missing-attribute]
        assert [image.alt_text for image in gallery] == [
            "pierwsza",
            "druga",
        ]

    def test_zdjecie_glowne_jest_jedno_na_produkt(self, on_commit):
        product = PublishedProductFactory()
        add_image(product=product, on_commit=on_commit, is_primary=True)

        with pytest.raises(IntegrityError):
            add_image(product=product, on_commit=on_commit, is_primary=True)

    def test_dwa_produkty_moga_miec_swoje_glowne(self, on_commit):
        first = add_image(on_commit=on_commit, is_primary=True)
        second = add_image(on_commit=on_commit, is_primary=True)

        assert first.is_primary and second.is_primary

    def test_zdjecie_moze_nalezec_do_wariantu(self, on_commit):
        product = PublishedProductFactory()
        variant = ProductVariantFactory(product=product)

        image = add_image(product=product, on_commit=on_commit, variant=variant)

        assert image.variant == variant

    def test_wariant_z_innego_produktu_jest_odrzucony(self):
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

    def test_produkt_zwraca_galerie_z_adresami(self, api_client, on_commit):
        product = PublishedProductFactory()
        add_image(product=product, on_commit=on_commit, alt_text="Pierścionek")

        body = self._detail(api_client, product.slug)

        assert len(body["images"]) == 1
        assert sorted(body["images"][0]["urls"]) == ["1600", "400", "800"]
        assert body["images"][0]["altText"] == "Pierścionek"

    def test_adresy_wskazuja_bucket_publiczny_bez_podpisu(self, api_client, on_commit):
        product = PublishedProductFactory()
        add_image(product=product, on_commit=on_commit)

        body = self._detail(api_client, product.slug)
        url = body["images"][0]["urls"]["800"]

        assert "X-Amz-Signature" not in url
        assert url.endswith("-800.webp")

    def test_zdjecie_w_przetwarzaniu_jest_pomijane(self, api_client):
        product = PublishedProductFactory()
        add_image(product=product)

        body = self._detail(api_client, product.slug)

        assert body["images"] == []

    def test_wariant_zwraca_swoje_zdjecia(self, api_client, on_commit):
        product = PublishedProductFactory()
        variant = ProductVariantFactory(product=product)
        add_image(product=product, on_commit=on_commit, variant=variant)

        body = self._detail(api_client, product.slug)

        assert len(body["variants"][0]["images"]) == 1

    def test_zdjecie_produktu_nie_wchodzi_do_wariantu(self, api_client, on_commit):
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
