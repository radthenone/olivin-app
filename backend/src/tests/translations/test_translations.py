"""Tłumaczenia katalogu — wyzwalacze, poprawki ręczne, fallback."""

from __future__ import annotations

from typing import Any

import pytest
from django.urls import reverse
from datetime import timedelta

from django.utils import timezone

from apps.products.models import ProductStatus
from apps.translations.language import language_from
from apps.translations.models import (
    SOURCE_LANGUAGE,
    Language,
    Translation,
    TranslationSource,
)
from apps.translations.registry import TRANSLATABLE_FIELDS, fields_for
from apps.translations.service import missing_fields, translate_object, translated_value
from apps.translations.tasks import translate_published_catalog
from apps.translations.warnings import stale_manual_fields
from tests.factories.categories import CategoryFactory
from tests.factories.collections import CollectionFactory
from tests.factories.products import ProductFactory, PublishedProductFactory

PREFIX = "EN:"


class FakeProvider:
    """Adapter fałszywy: przewidywalny i liczy wywołania.

    Prawdziwy silnik wymagałby sieci i klucza, a test i tak sprawdza nasze
    reguły — kiedy tłumaczymy i czego nie ruszamy — a nie jakość przekładu.
    """

    calls: list[list[str]] = []

    def translate(self, texts, *, target_language, source_language):
        type(self).calls.append(list(texts))
        return [f"{PREFIX}{text}" for text in texts]


@pytest.fixture(autouse=True)
def fake_provider(settings):
    FakeProvider.calls = []
    settings.TRANSLATION_PROVIDER = "tests.translations.test_translations.FakeProvider"
    return FakeProvider


@pytest.fixture
def on_commit(django_capture_on_commit_callbacks):
    return django_capture_on_commit_callbacks


def _get(client, url: str, **params: Any) -> dict[str, Any]:
    response: Any = client.get(url, params or None)
    assert response.status_code == 200, response.content
    return response.json()


def add_translation(obj, field: str, text: str, source=TranslationSource.AUTO):
    from django.contrib.contenttypes.models import ContentType

    return Translation.objects.create(
        content_type=ContentType.objects.get_for_model(obj),
        object_id=obj.pk,
        field=field,
        language=Language.EN,
        text=text,
        source=source,
    )


class TestRegistry:
    """Tłumaczymy nazwę i opis produktu, opis zdjęcia, nazwy kategorii i kolekcji."""

    def test_objete_pola(self):
        assert TRANSLATABLE_FIELDS == {
            "products.Product": ("name", "description"),
            "products.ProductImage": ("alt_text",),
            "categories.Category": ("name",),
            "collections.Collection": ("name",),
        }

    def test_slug_nie_jest_tlumaczony(self):
        for fields in TRANSLATABLE_FIELDS.values():
            assert "slug" not in fields


@pytest.mark.django_db
class TestTranslateObject:
    """Uzupełnianie brakujących tłumaczeń."""

    def test_tlumaczy_puste_pola(self):
        product = PublishedProductFactory(name="Pierścionek", description="Złoty")

        created = translate_object(product)

        assert created == 2
        assert translated_value(product, "name", "en") == "EN:Pierścionek"

    def test_nie_tlumaczy_pustego_tekstu(self):
        product = PublishedProductFactory(name="Pierścionek", description="")

        translate_object(product)

        assert [t.field for t in product.translations.all()] == ["name"]

    def test_nie_nadpisuje_istniejacego(self):
        product = PublishedProductFactory(name="Pierścionek", description="Złoty")
        add_translation(product, "name", "Ring")

        translate_object(product)
        product.refresh_from_db()

        assert translated_value(product, "name", "en") == "Ring"

    def test_nie_nadpisuje_poprawki_recznej(self):
        """Właściciel poprawia tłumaczenie, bo automat się pomylił."""
        product = PublishedProductFactory(name="Pierścionek", description="Złoty")
        add_translation(product, "name", "Gold ring", TranslationSource.MANUAL)

        translate_object(product)
        product.refresh_from_db()

        assert translated_value(product, "name", "en") == "Gold ring"
        assert product.translations.get(field="name").is_manual

    def test_drugi_przebieg_nie_wola_silnika(self):
        product = PublishedProductFactory(name="Pierścionek", description="Złoty")
        translate_object(product)
        FakeProvider.calls = []

        translate_object(product)

        assert FakeProvider.calls == []

    def test_nazwa_i_opis_ida_jednym_wywolaniem(self):
        product = PublishedProductFactory(name="Pierścionek", description="Złoty")

        translate_object(product)

        assert len(FakeProvider.calls) == 1

    def test_jedno_tlumaczenie_na_pole_i_jezyk(self):
        from django.db.utils import IntegrityError

        product = PublishedProductFactory(name="Pierścionek")
        add_translation(product, "name", "Ring")

        with pytest.raises(IntegrityError):
            add_translation(product, "name", "Inne")

    def test_brakujace_pola_widac_przed_tlumaczeniem(self):
        product = PublishedProductFactory(name="Pierścionek", description="Złoty")

        assert sorted(missing_fields(product)) == ["description", "name"]

    def test_kategoria_i_kolekcja_tez_maja_swoje_pola(self):
        assert fields_for(CategoryFactory()) == ("name",)
        assert fields_for(CollectionFactory()) == ("name",)


@pytest.mark.django_db
class TestPublishTrigger:
    """Wyzwalacz pierwszy: przejście produktu na opublikowany."""

    def test_publikacja_kolejkuje_tlumaczenie(self, on_commit):
        product = ProductFactory(name="Pierścionek", description="Złoty")

        with on_commit(execute=True):
            product.status = ProductStatus.PUBLISHED
            product.save()

        assert translated_value(product, "name", "en") == "EN:Pierścionek"

    def test_szkic_nie_jest_tlumaczony(self, on_commit):
        with on_commit(execute=True):
            product = ProductFactory(name="Pierścionek", description="Złoty")

        assert product.translations.count() == 0

    def test_zapis_opublikowanego_nie_kolejkuje_ponownie(self, on_commit):
        with on_commit(execute=True):
            product = PublishedProductFactory(name="Pierścionek", description="Złoty")
        FakeProvider.calls = []

        with on_commit(execute=True):
            product.name = "Pierścionek złoty"
            product.save()

        assert FakeProvider.calls == []

    def test_publikacja_obejmuje_opisy_zdjec(self, on_commit):
        from tests.products.test_images import add_image

        product = ProductFactory(name="Pierścionek", description="Złoty")
        image = add_image(product=product, alt_text="Złoty pierścionek z brylantem")

        with on_commit(execute=True):
            product.status = ProductStatus.PUBLISHED
            product.save()

        image.refresh_from_db()
        assert translated_value(image, "alt_text", "en").startswith(PREFIX)


@pytest.mark.django_db
class TestPeriodicTrigger:
    """Wyzwalacz drugi: obchód opublikowanego katalogu."""

    def test_uzupelnia_brakujace(self):
        product = PublishedProductFactory(name="Pierścionek", description="Złoty")

        translate_published_catalog()  # type: ignore[missing-argument]

        assert sorted(t.field for t in product.translations.all()) == [
            "description",
            "name",
        ]

    def test_pomija_szkice(self):
        """Obchód dotyka kategorii produktu, bo ta jest zawsze widoczna —
        ale sam szkic zostaje nieprzetłumaczony."""
        draft = ProductFactory(name="Szkic", description="Opis")

        translate_published_catalog()  # type: ignore[missing-argument]

        assert draft.translations.count() == 0

    def test_obejmuje_kategorie_i_kolekcje(self):
        CategoryFactory(name="Pierścionki")
        CollectionFactory(name="Zima", description="")

        assert translate_published_catalog() == 2  # type: ignore[missing-argument]

    def test_drugi_obchod_niczego_nie_doklada(self):
        PublishedProductFactory(name="Pierścionek", description="Złoty")
        translate_published_catalog()  # type: ignore[missing-argument]

        assert translate_published_catalog() == 0  # type: ignore[missing-argument]

    def test_nie_rusza_poprawek_recznych(self):
        product = PublishedProductFactory(name="Pierścionek", description="Złoty")
        add_translation(product, "name", "Gold ring", TranslationSource.MANUAL)

        translate_published_catalog()  # type: ignore[missing-argument]
        product.refresh_from_db()

        assert translated_value(product, "name", "en") == "Gold ring"


class TestLanguageResolution:
    """`?lang=` ma pierwszeństwo przed `Accept-Language`."""

    class FakeRequest:
        def __init__(self, params=None, headers=None):
            self.query_params = params or {}
            self.headers = headers or {}

    def test_parametr_w_adresie(self):
        assert language_from(self.FakeRequest({"lang": "en"})) == "en"

    def test_naglowek_gdy_brak_parametru(self):
        request = self.FakeRequest(headers={"Accept-Language": "en-GB,en;q=0.9"})

        assert language_from(request) == "en"

    def test_parametr_wygrywa_z_naglowkiem(self):
        request = self.FakeRequest(
            {"lang": "pl"}, {"Accept-Language": "en-GB,en;q=0.9"}
        )

        assert language_from(request) == "pl"

    def test_jezyk_spoza_listy_schodzi_do_polskiego(self):
        assert language_from(self.FakeRequest({"lang": "de"})) == SOURCE_LANGUAGE

    def test_brak_zadania_to_polski(self):
        assert language_from(None) == SOURCE_LANGUAGE


@pytest.mark.django_db
class TestCatalogApi:
    """API katalogu podaje pola w wybranym języku z odwrotem na polski."""

    def test_domyslnie_po_polsku(self, api_client):
        product = PublishedProductFactory(name="Pierścionek", description="Złoty")
        translate_object(product)

        body = _get(
            api_client, reverse("product-detail", kwargs={"slug": product.slug})
        )

        assert body["name"] == "Pierścionek"

    def test_lang_en_zwraca_tlumaczenie(self, api_client):
        product = PublishedProductFactory(name="Pierścionek", description="Złoty")
        translate_object(product)

        body = _get(
            api_client,
            reverse("product-detail", kwargs={"slug": product.slug}),
            lang="en",
        )

        assert body["name"] == "EN:Pierścionek"
        assert body["description"] == "EN:Złoty"

    def test_fallback_na_polski_gdy_brak_tlumaczenia(self, api_client):
        """Świeżo opublikowany produkt ma być czytelny, zanim zadanie skończy."""
        product = PublishedProductFactory(name="Pierścionek", description="Złoty")

        body = _get(
            api_client,
            reverse("product-detail", kwargs={"slug": product.slug}),
            lang="en",
        )

        assert body["name"] == "Pierścionek"

    def test_slug_nie_jest_tlumaczony(self, api_client):
        product = PublishedProductFactory(name="Pierścionek", description="Złoty")
        translate_object(product)

        body = _get(
            api_client,
            reverse("product-detail", kwargs={"slug": product.slug}),
            lang="en",
        )

        assert body["slug"] == product.slug

    def test_naglowek_tez_dziala(self, api_client):
        product = PublishedProductFactory(name="Pierścionek", description="Złoty")
        translate_object(product)

        response: Any = api_client.get(
            reverse("product-detail", kwargs={"slug": product.slug}),
            headers={"Accept-Language": "en"},
        )

        assert response.json()["name"] == "EN:Pierścionek"

    def test_lista_produktow_tez_tlumaczy(self, api_client):
        product = PublishedProductFactory(name="Pierścionek", description="Złoty")
        translate_object(product)

        body = _get(api_client, reverse("product-list"), lang="en")

        assert body["results"][0]["name"] == "EN:Pierścionek"

    def test_kategorie_tlumacza_sie(self, api_client):
        category = CategoryFactory(name="Pierścionki")
        translate_object(category)

        body = _get(api_client, reverse("category-list"), lang="en")

        assert body[0]["name"] == "EN:Pierścionki"  # type: ignore[bad-index]

    def test_kolekcje_tlumacza_sie(self, api_client):
        collection = CollectionFactory(
            name="Zima", products=[PublishedProductFactory()]
        )
        translate_object(collection)

        body = _get(api_client, reverse("collection-list"), lang="en")

        assert body["results"][0]["name"] == "EN:Zima"

    def test_tlumaczenia_nie_mnoza_zapytan(
        self, api_client, django_assert_max_num_queries
    ):
        for index in range(5):
            product = PublishedProductFactory(
                name=f"Pierścionek {index}", description="Złoty"
            )
            translate_object(product)

        with django_assert_max_num_queries(9):
            api_client.get(reverse("product-list"), {"lang": "en"})


@pytest.mark.django_db
class TestAdminMarksManual:
    """Zapis tłumaczenia z panelu oznacza je jako poprawione ręcznie.

    Znakowanie siedzi w zbiorze formularzy inline'u, bo `InlineModelAdmin`
    nie ma `save_model` — wcześniejsza wersja ustawiała źródło w metodzie,
    której nic nie woła.
    """

    def _formset(self, product, data):
        """Zbiór formularzy taki, jaki panel buduje dla tego inline'u.

        Składany wprost, a nie przez `get_formset`: tamta droga sprawdza
        uprawnienia i potrzebuje żądania z użytkownikiem, a sprawdzane jest
        zachowanie zapisu, nie panel.
        """
        from django.contrib.contenttypes.forms import generic_inlineformset_factory

        from apps.translations.admin import TranslationInline

        formset_class = generic_inlineformset_factory(
            Translation,
            formset=TranslationInline.formset,
            ct_field=TranslationInline.ct_field,
            fk_field=TranslationInline.ct_fk_field,
            fields=("field", "language", "text"),
            extra=0,
        )
        return formset_class(data=data, instance=product)

    def test_nowy_wpis_z_panelu_jest_reczny(self):
        product = PublishedProductFactory(name="Pierścionek", description="Złoty")
        prefix = "translations-translation-content_type-object_id"
        formset = self._formset(
            product,
            {
                f"{prefix}-TOTAL_FORMS": "1",
                f"{prefix}-INITIAL_FORMS": "0",
                f"{prefix}-0-field": "name",
                f"{prefix}-0-language": "en",
                f"{prefix}-0-text": "Gold ring",
            },
        )

        assert formset.is_valid(), formset.errors
        formset.save()

        assert product.translations.get(field="name").is_manual

    def test_poprawka_istniejacego_staje_sie_reczna(self):
        product = PublishedProductFactory(name="Pierścionek", description="Złoty")
        translate_object(product)
        translation = product.translations.get(field="name")
        prefix = "translations-translation-content_type-object_id"
        formset = self._formset(
            product,
            {
                f"{prefix}-TOTAL_FORMS": "1",
                f"{prefix}-INITIAL_FORMS": "1",
                f"{prefix}-0-id": str(translation.pk),
                f"{prefix}-0-field": "name",
                f"{prefix}-0-language": "en",
                f"{prefix}-0-text": "Gold ring",
            },
        )

        assert formset.is_valid(), formset.errors
        formset.save()

        translation.refresh_from_db()
        assert translation.is_manual
        assert translation.text == "Gold ring"

    def test_automat_juz_tego_nie_nadpisze(self):
        product = PublishedProductFactory(name="Pierścionek", description="Złoty")
        translate_object(product)
        product.translations.filter(field="name").update(
            source=TranslationSource.MANUAL, text="Gold ring"
        )

        translate_published_catalog()  # type: ignore[missing-argument]

        assert translated_value(product, "name", "en") == "Gold ring"


@pytest.mark.django_db
class TestStaleManualWarning:
    """Zmiana tekstu polskiego przy poprawce ręcznej wymaga ostrzeżenia."""

    def test_poprawka_starsza_od_zmiany_jest_zglaszana(self):
        product = PublishedProductFactory(name="Pierścionek", description="Złoty")
        translation = add_translation(
            product, "name", "Gold ring", TranslationSource.MANUAL
        )
        Translation.objects.filter(pk=translation.pk).update(
            translated_at=timezone.now() - timedelta(days=1)
        )

        product.name = "Pierścionek złoty"
        product.save()

        assert stale_manual_fields(product) == ["name"]

    def test_swieza_poprawka_nie_jest_zglaszana(self):
        product = PublishedProductFactory(name="Pierścionek", description="Złoty")
        add_translation(product, "name", "Gold ring", TranslationSource.MANUAL)

        assert stale_manual_fields(product) == []

    def test_tlumaczenie_automatyczne_nie_jest_zglaszane(self):
        """Automat i tak je poprawi przy następnym obchodzie."""
        product = PublishedProductFactory(name="Pierścionek", description="Złoty")
        translation = add_translation(product, "name", "Ring")
        Translation.objects.filter(pk=translation.pk).update(
            translated_at=timezone.now() - timedelta(days=1)
        )

        product.name = "Pierścionek złoty"
        product.save()

        assert stale_manual_fields(product) == []
