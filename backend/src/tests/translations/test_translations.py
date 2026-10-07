"""Tłumaczenia katalogu — wyzwalacze, poprawki ręczne, fallback."""

from __future__ import annotations

from typing import Any

import pytest
from django.urls import reverse
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
        """Zwraca przewidywalne tłumaczenie i liczy wywołanie."""
        type(self).calls.append(list(texts))
        return [f"{PREFIX}{text}" for text in texts]


@pytest.fixture(autouse=True)
def fake_provider(settings):
    """Fałszywy silnik tłumaczeń podpięty w ustawieniach."""
    FakeProvider.calls = []
    settings.TRANSLATION_PROVIDER = "tests.translations.test_translations.FakeProvider"
    return FakeProvider


@pytest.fixture
def on_commit(django_capture_on_commit_callbacks):
    """Uruchamia od razu to, co czeka na zatwierdzenie transakcji."""
    return django_capture_on_commit_callbacks


def _get(client, url: str, **params: Any) -> dict[str, Any]:
    response: Any = client.get(url, params or None)
    assert response.status_code == 200, response.content
    return response.json()


def add_translation(obj, field: str, text: str, source=TranslationSource.AUTO):
    """Ustawia tłumaczenie, nadpisując istniejące.

    Nadpisuje, a nie tworzy: publikacja produktu tłumaczy nazwę od razu,
    żeby zbudować z niej adres, więc wpis dla `name` zwykle już jest.
    """
    from django.contrib.contenttypes.models import ContentType

    translation, _ = Translation.objects.update_or_create(
        content_type=ContentType.objects.get_for_model(obj),
        object_id=obj.pk,
        field=field,
        language=Language.EN,
        defaults={
            "text": text,
            "source": source,
            "translated_at": timezone.now(),
        },
    )
    return translation


class TestRegistry:
    """Tłumaczymy nazwę i opis produktu, opis zdjęcia, nazwy kategorii i kolekcji."""

    def test_covered_fields(self):
        """Pola objęte tłumaczeniem."""
        assert TRANSLATABLE_FIELDS == {
            "products.Product": ("name", "description"),
            "products.ProductImage": ("alt_text",),
            "categories.Category": ("name",),
            "collections.Collection": ("name",),
        }

    def test_slug_is_not_translated(self):
        """Slug nie jest tłumaczony."""
        for fields in TRANSLATABLE_FIELDS.values():
            assert "slug" not in fields


@pytest.mark.django_db
class TestTranslateObject:
    """Uzupełnianie brakujących tłumaczeń."""

    def test_translates_empty_fields(self):
        """Tłumaczy puste pola."""
        product = ProductFactory(name="Pierścionek", description="Złoty")

        created = translate_object(product)

        assert created == 2
        assert translated_value(product, "name", "en") == "EN:Pierścionek"

    def test_publishing_keeps_translated_name(self):
        """Adres powstaje z nazwy angielskiej, więc publikacja tłumaczy ją
        od razu — zadaniu w tle zostaje sam opis."""
        product = PublishedProductFactory(name="Pierścionek", description="Złoty")

        assert missing_fields(product) == ["description"]

    def test_does_not_translate_empty_text(self):
        """Nie tłumaczy pustego tekstu."""
        product = ProductFactory(name="Pierścionek", description="")

        translate_object(product)

        assert [t.field for t in product.translations.all()] == ["name"]

    def test_does_not_overwrite_existing(self):
        """Nie nadpisuje istniejącego tłumaczenia."""
        product = ProductFactory(name="Pierścionek", description="Złoty")
        add_translation(product, "name", "Ring")

        translate_object(product)
        product.refresh_from_db()

        assert translated_value(product, "name", "en") == "Ring"

    def test_does_not_overwrite_manual_fix(self):
        """Tłumaczenie poprawione ręcznie nie jest nadpisywane.

        Właściciel poprawia tłumaczenie, bo automat się pomylił.
        """
        product = ProductFactory(name="Pierścionek", description="Złoty")
        add_translation(product, "name", "Gold ring", TranslationSource.MANUAL)

        translate_object(product)
        product.refresh_from_db()

        assert translated_value(product, "name", "en") == "Gold ring"
        assert product.translations.get(field="name").is_manual

    def test_second_run_does_not_call_engine(self):
        """Drugi przebieg nie woła silnika."""
        product = ProductFactory(name="Pierścionek", description="Złoty")
        translate_object(product)
        FakeProvider.calls = []

        translate_object(product)

        assert FakeProvider.calls == []

    def test_name_and_description_in_one_call(self):
        """Nazwa i opis idą jednym wywołaniem."""
        product = ProductFactory(name="Pierścionek", description="Złoty")
        # Kategoria produktu ma własny adres, więc jej nazwa poszła do silnika
        # przy zakładaniu — liczymy tylko to, co robi `translate_object`.
        FakeProvider.calls = []

        translate_object(product)

        assert len(FakeProvider.calls) == 1

    def test_one_translation_per_field_and_language(self):
        """Jedno tłumaczenie na pole i język."""
        from django.contrib.contenttypes.models import ContentType
        from django.db.utils import IntegrityError

        product = ProductFactory(name="Pierścionek")
        add_translation(product, "name", "Ring")

        with pytest.raises(IntegrityError):
            Translation.objects.create(
                content_type=ContentType.objects.get_for_model(product),
                object_id=product.pk,
                field="name",
                language=Language.EN,
                text="Inne",
            )

    def test_missing_fields_are_visible_before_translation(self):
        """Brakujące pola widać przed tłumaczeniem."""
        product = ProductFactory(name="Pierścionek", description="Złoty")

        assert sorted(missing_fields(product)) == ["description", "name"]

    def test_category_and_collection_have_fields_too(self):
        """Kategoria i kolekcja też mają swoje pola."""
        assert fields_for(CategoryFactory()) == ("name",)
        assert fields_for(CollectionFactory()) == ("name",)


@pytest.mark.django_db
class TestPublishTrigger:
    """Wyzwalacz pierwszy: przejście produktu na opublikowany."""

    def test_publishing_queues_translation(self, on_commit):
        """Publikacja kolejkuje tłumaczenie."""
        product = ProductFactory(name="Pierścionek", description="Złoty")

        with on_commit(execute=True):
            product.status = ProductStatus.PUBLISHED
            product.save()

        assert translated_value(product, "name", "en") == "EN:Pierścionek"

    def test_draft_is_not_translated(self, on_commit):
        """Szkic nie jest tłumaczony."""
        with on_commit(execute=True):
            product = ProductFactory(name="Pierścionek", description="Złoty")

        assert product.translations.count() == 0

    def test_saving_published_does_not_queue_again(self, on_commit):
        """Zapis opublikowanego nie kolejkuje ponownie."""
        with on_commit(execute=True):
            product = PublishedProductFactory(name="Pierścionek", description="Złoty")
        FakeProvider.calls = []

        with on_commit(execute=True):
            product.name = "Pierścionek złoty"
            product.save()

        assert FakeProvider.calls == []

    def test_publishing_covers_image_descriptions(self, on_commit):
        """Publikacja obejmuje opisy zdjęć."""
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

    def test_fills_missing(self):
        """Obchód uzupełnia brakujące tłumaczenia."""
        product = PublishedProductFactory(name="Pierścionek", description="Złoty")

        translate_published_catalog()  # type: ignore[missing-argument]

        assert sorted(t.field for t in product.translations.all()) == [
            "description",
            "name",
        ]

    def test_skips_drafts(self):
        """Obchód dotyka kategorii produktu, bo ta jest zawsze widoczna —
        ale sam szkic zostaje nieprzetłumaczony."""
        draft = ProductFactory(name="Szkic", description="Opis")

        translate_published_catalog()  # type: ignore[missing-argument]

        assert draft.translations.count() == 0

    def test_covers_categories_and_collections(self):
        """Nazwy są przetłumaczone już przy zakładaniu, bo z nich powstaje
        adres — obchód ma wtedy jawnie nic do roboty."""
        CategoryFactory(name="Pierścionki")
        CollectionFactory(name="Zima", description="")

        assert translate_published_catalog() == 0  # type: ignore[missing-argument]

    def test_sweep_adds_field_added_after_publishing(self):
        """Obchód dokłada tłumaczenie dopisane po publikacji."""
        product = PublishedProductFactory(name="Pierścionek", description="")
        product.description = "Złoty, próba 585"
        product.save()

        assert translate_published_catalog() == 1  # type: ignore[missing-argument]
        assert translated_value(product, "description", "en").startswith(PREFIX)

    def test_second_sweep_adds_nothing(self):
        """Drugi obchód niczego nie dokłada."""
        PublishedProductFactory(name="Pierścionek", description="Złoty")
        translate_published_catalog()  # type: ignore[missing-argument]

        assert translate_published_catalog() == 0  # type: ignore[missing-argument]

    def test_keeps_manual_fixes(self):
        """Obchód nie rusza poprawek ręcznych."""
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

    def test_query_param(self):
        """Język z parametru w adresie."""
        assert language_from(self.FakeRequest({"lang": "en"})) == "en"

    def test_header_without_param(self):
        """Język z nagłówka, gdy brak parametru."""
        request = self.FakeRequest(headers={"Accept-Language": "en-GB,en;q=0.9"})

        assert language_from(request) == "en"

    def test_param_beats_header(self):
        """Parametr wygrywa z nagłówkiem."""
        request = self.FakeRequest(
            {"lang": "pl"}, {"Accept-Language": "en-GB,en;q=0.9"}
        )

        assert language_from(request) == "pl"

    def test_unknown_language_falls_back_to_polish(self):
        """Język spoza listy schodzi do polskiego."""
        assert language_from(self.FakeRequest({"lang": "de"})) == SOURCE_LANGUAGE

    def test_no_request_means_polish(self):
        """Brak żądania to polski."""
        assert language_from(None) == SOURCE_LANGUAGE


@pytest.mark.django_db
class TestCatalogApi:
    """API katalogu podaje pola w wybranym języku z odwrotem na polski."""

    def test_polish_by_default(self, api_client):
        """Domyślnie po polsku."""
        product = PublishedProductFactory(name="Pierścionek", description="Złoty")
        translate_object(product)

        body = _get(
            api_client, reverse("product-detail", kwargs={"slug": product.slug})
        )

        assert body["name"] == "Pierścionek"

    def test_lang_en_returns_translation(self, api_client):
        """`lang=en` zwraca tłumaczenie."""
        product = PublishedProductFactory(name="Pierścionek", description="Złoty")
        translate_object(product)

        body = _get(
            api_client,
            reverse("product-detail", kwargs={"slug": product.slug}),
            lang="en",
        )

        assert body["name"] == "EN:Pierścionek"
        assert body["description"] == "EN:Złoty"

    def test_falls_back_to_polish_without_translation(self, api_client):
        """Świeżo opublikowany produkt ma być czytelny, zanim zadanie skończy.

        Opis, a nie nazwa: nazwa jest tłumaczona już przy publikacji, bo
        z niej powstaje adres. Opis czeka na zadanie w tle.
        """
        product = PublishedProductFactory(name="Pierścionek", description="Złoty")

        body = _get(
            api_client,
            reverse("product-detail", kwargs={"slug": product.slug}),
            lang="en",
        )

        assert body["description"] == "Złoty"

    def test_slug_is_not_translated(self, api_client):
        """Slug nie jest tłumaczony."""
        product = PublishedProductFactory(name="Pierścionek", description="Złoty")
        translate_object(product)

        body = _get(
            api_client,
            reverse("product-detail", kwargs={"slug": product.slug}),
            lang="en",
        )

        assert body["slug"] == product.slug

    def test_header_works_too(self, api_client):
        """Nagłówek też działa."""
        product = PublishedProductFactory(name="Pierścionek", description="Złoty")
        translate_object(product)

        response: Any = api_client.get(
            reverse("product-detail", kwargs={"slug": product.slug}),
            headers={"Accept-Language": "en"},
        )

        assert response.json()["name"] == "EN:Pierścionek"

    def test_product_list_is_translated_too(self, api_client):
        """Lista produktów też jest tłumaczona."""
        product = PublishedProductFactory(name="Pierścionek", description="Złoty")
        translate_object(product)

        body = _get(api_client, reverse("product-list"), lang="en")

        assert body["results"][0]["name"] == "EN:Pierścionek"

    def test_categories_are_translated(self, api_client):
        """Kategorie się tłumaczą."""
        category = CategoryFactory(name="Pierścionki")
        translate_object(category)

        body = _get(api_client, reverse("category-list"), lang="en")

        assert body[0]["name"] == "EN:Pierścionki"  # type: ignore[bad-index]

    def test_collections_are_translated(self, api_client):
        """Kolekcje się tłumaczą."""
        collection = CollectionFactory(
            name="Zima", products=[PublishedProductFactory()]
        )
        translate_object(collection)

        body = _get(api_client, reverse("collection-list"), lang="en")

        assert body["results"][0]["name"] == "EN:Zima"

    def test_translations_do_not_multiply_queries(
        self, api_client, django_assert_max_num_queries
    ):
        """Tłumaczenia nie mnożą zapytań."""
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

    def test_new_admin_entry_is_manual(self):
        """Nowy wpis z panelu jest ręczny."""
        product = PublishedProductFactory(name="Pierścionek", description="Złoty")
        prefix = "translations-translation-content_type-object_id"
        formset = self._formset(
            product,
            {
                f"{prefix}-TOTAL_FORMS": "1",
                f"{prefix}-INITIAL_FORMS": "0",
                f"{prefix}-0-field": "description",
                f"{prefix}-0-language": "en",
                f"{prefix}-0-text": "Gold, 585",
            },
        )

        assert formset.is_valid(), formset.errors
        formset.save()

        assert product.translations.get(field="description").is_manual

    def test_edit_of_existing_becomes_manual(self):
        """Poprawka istniejącego staje się ręczna."""
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

    def test_engine_will_not_overwrite_it(self):
        """Automat już tego nie nadpisze."""
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

    def test_changed_name_with_manual_fix_is_reported(self):
        """Zmieniona nazwa przy poprawce ręcznej jest zgłaszana."""
        product = PublishedProductFactory(name="Pierścionek", description="Złoty")
        add_translation(product, "name", "Gold ring", TranslationSource.MANUAL)

        assert stale_manual_fields(product, ["name"]) == ["name"]

    def test_unchanged_name_is_not_reported(self):
        """Niezmieniona nazwa nie jest zgłaszana.

        Ostrzeżenie przy każdym zapisie przestałoby cokolwiek znaczyć.
        """
        product = PublishedProductFactory(name="Pierścionek", description="Złoty")
        add_translation(product, "name", "Gold ring", TranslationSource.MANUAL)

        assert stale_manual_fields(product, ["price"]) == []

    def test_automatic_translation_is_not_reported(self):
        """Automat i tak je poprawi przy następnym obchodzie."""
        product = PublishedProductFactory(name="Pierścionek", description="Złoty")
        add_translation(product, "name", "Ring")

        assert stale_manual_fields(product, ["name"]) == []

    def test_unlisted_field_is_not_reported(self):
        """Pole spoza listy nie jest zgłaszane."""
        product = PublishedProductFactory(name="Pierścionek", description="Złoty")
        add_translation(product, "name", "Gold ring", TranslationSource.MANUAL)

        assert stale_manual_fields(product, ["slug", "status"]) == []
