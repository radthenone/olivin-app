from __future__ import annotations

from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

from apps.categories.models import Category
from common.money import Money
from tests.factories.categories import CategoryFactory


@pytest.mark.django_db
class TestSlug:
    """Slug jest angielskim adresem kategorii — jeden, unikalny, niezmienny."""

    def test_slug_is_built_from_english_name(self):
        """Nie z nazwy polskiej pozbawionej ogonków — adres ma być angielski
        (`.ai/project.md`), a slug jest niezmienny, więc pomyłka zostaje."""
        category = CategoryFactory(name="Pierścionki")

        assert category.slug == "en-pierscionki"

    def test_polish_name_is_not_used_in_slug(self):
        """Polska nazwa nie trafia wprost do adresu."""
        category = CategoryFactory(name="Pierścionki zaręczynowe")

        assert category.slug != "pierscionki-zareczynowe"

    def test_entered_slug_is_kept(self):
        """Wpisany slug zostaje nietknięty."""
        category = CategoryFactory(name="Pierścionki złote", slug="gold-rings")

        assert category.slug == "gold-rings"

    def test_slug_change_after_save_is_rejected_for_engine_slug(self):
        """Zmiana sluga po zapisie jest odrzucana także przy slugu z silnika."""
        category = CategoryFactory(name="Pierścionki")

        category.slug = "other-rings"
        with pytest.raises(ValidationError):
            category.save()

    def test_collision_gets_suffix(self):
        """Kolizja slugów dostaje przyrostek."""
        CategoryFactory(name="Rings")
        second = CategoryFactory(name="Rings")

        assert second.slug == "en-rings-2"

    def test_slug_is_not_built_without_english_name(self, settings):
        """Cichy odwrót do nazwy polskiej byłby dokładnie tym błędem, który
        ta warstwa ma usuwać — więc zapis jest odrzucany."""
        settings.TRANSLATION_PROVIDER = "tests.shared.translation.BrokenProvider"

        with pytest.raises(ValidationError) as error:
            CategoryFactory(name="Pierścionki")

        assert "slug" in error.value.message_dict

    def test_manual_slug_works_without_engine(self, settings):
        """Jedyna droga niezależna od sieci — i dlatego ma pierwszeństwo."""
        settings.TRANSLATION_PROVIDER = "tests.shared.translation.BrokenProvider"

        category = CategoryFactory(name="Pierścionki", slug="engagement-rings")

        assert category.slug == "engagement-rings"

    def test_existing_translation_skips_engine(self, settings):
        """Gotowe tłumaczenie nie wywołuje silnika."""
        from django.contrib.contenttypes.models import ContentType

        from apps.translations.models import Translation

        category = CategoryFactory(name="Pierścionki", slug="rings")
        Translation.objects.create(
            content_type=ContentType.objects.get_for_model(category),
            object_id=category.pk,
            field="name",
            language="en",
            text="Engagement rings",
        )
        settings.TRANSLATION_PROVIDER = "tests.shared.translation.BrokenProvider"

        second = Category(name="Pierścionki")
        second.slug = ""
        # Tłumaczenie należy do innego obiektu, więc silnik i tak byłby
        # potrzebny — sprawdzamy, że nie sięga po cudze.
        with pytest.raises(ValidationError):
            second.save()

    def test_slug_change_after_save_is_rejected(self):
        """Zmiana sluga po zapisie jest odrzucana."""
        category = CategoryFactory(name="Gold rings")

        category.slug = "silver-rings"
        with pytest.raises(ValidationError) as error:
            category.save()

        assert "slug" in error.value.message_dict

    def test_save_without_slug_change_passes(self):
        """Zapis bez zmiany sluga przechodzi."""
        category = CategoryFactory(name="Rings", slug="rings")

        category.name = "Złote pierścionki"
        category.save()

        category.refresh_from_db()
        assert category.slug == "rings"
        assert category.name == "Złote pierścionki"

    def test_slug_is_unique_in_database(self):
        """Slug jest unikalny w bazie."""
        CategoryFactory(slug="gold-rings")

        with pytest.raises(IntegrityError):
            Category.objects.create(name="Inne", slug="gold-rings")


@pytest.mark.django_db
class TestTree:
    """Drzewo jest listą sąsiedztwa: rodzic opcjonalny, potomkowie przez relację."""

    def test_category_without_parent_is_root(self):
        """Kategoria bez rodzica jest korzeniem."""
        root = CategoryFactory(name="Biżuteria")

        assert root.parent is None
        assert list(Category.objects.filter(parent__isnull=True)) == [root]

    def test_children_are_available_through_relation(self):
        """Potomkowie są dostępni przez relację."""
        root = CategoryFactory(name="Biżuteria")
        child = CategoryFactory(name="Pierścionki", parent=root)

        assert list(Category.objects.filter(parent=root)) == [child]
        assert child.parent == root

    def test_tree_has_many_levels(self):
        """Drzewo ma wiele poziomów."""
        root = CategoryFactory(name="Biżuteria")
        middle = CategoryFactory(name="Pierścionki", parent=root)
        leaf = CategoryFactory(name="Zaręczynowe", parent=middle)

        assert leaf.parent is not None
        assert leaf.parent.parent == root

    def test_category_cannot_be_its_own_parent(self):
        """Kategoria nie może być swoim rodzicem."""
        category = CategoryFactory(name="Biżuteria")

        category.parent = category
        with pytest.raises(ValidationError) as error:
            category.full_clean()

        assert "parent" in error.value.message_dict

    def test_cycle_in_tree_is_rejected(self):
        """Pętla w drzewie jest odrzucana."""
        root = CategoryFactory(name="Biżuteria")
        child = CategoryFactory(name="Pierścionki", parent=root)

        root.parent = child
        with pytest.raises(ValidationError) as error:
            root.full_clean()

        assert "parent" in error.value.message_dict

    def test_cycle_is_rejected_on_plain_save(self):
        """`save()` nie woła `clean()`, a pętla to uszkodzenie danych:
        gałąź bez korzenia wypada z menu i rozkłada rekurencję przy odczycie."""
        root = CategoryFactory(name="Biżuteria")
        child = CategoryFactory(name="Pierścionki", parent=root)

        root.parent = child
        with pytest.raises(ValidationError) as error:
            root.save()

        assert "parent" in error.value.message_dict

    def test_category_cannot_become_own_parent_on_save(self):
        """Kategoria nie zostanie swoim rodzicem przez sam zapis."""
        category = CategoryFactory(name="Biżuteria")

        category.parent = category
        with pytest.raises(ValidationError):
            category.save()

    def test_deep_tree_saves_without_false_alarm(self):
        """Głębokie drzewo zapisuje się bez fałszywego alarmu."""
        node = CategoryFactory(name="Poziom 0")
        for depth in range(1, 12):
            node = CategoryFactory(name=f"Poziom {depth}", parent=node)

        node.name = "Poziom ostatni"
        node.save()

        assert Category.objects.count() == 12

    def test_category_with_children_is_not_deleted_silently(self):
        """Kategoria z potomkami nie znika po cichu."""
        from django.db.models import ProtectedError

        root = CategoryFactory(name="Biżuteria")
        CategoryFactory(name="Pierścionki", parent=root)

        with pytest.raises(ProtectedError):
            root.delete()


@pytest.mark.django_db
class TestMargin:
    """Narzut domyślny kategorii: procent albo kwota, nigdy oba (ADR 0022)."""

    def test_percent_margin(self):
        """Narzut procentowy."""
        category = CategoryFactory(margin_percent=Decimal("35.00"))

        assert category.margin_percent == Decimal("35.00")
        assert category.margin is None

    def test_amount_margin_is_money(self):
        """Narzut kwotowy jest pieniędzmi."""
        category = CategoryFactory(margin_amount=15000)

        assert category.margin == Money(15000, "PLN")

    def test_no_margin_is_allowed(self):
        """Brak narzutu jest dozwolony."""
        category = CategoryFactory()

        assert category.margin_percent is None
        assert category.margin is None

    def test_both_margins_are_rejected_by_validation(self):
        """Oba narzuty naraz są odrzucane w walidacji."""
        category = CategoryFactory.build(
            margin_percent=Decimal("35.00"), margin_amount=15000
        )

        with pytest.raises(ValidationError) as error:
            category.full_clean()

        assert "margin_amount" in error.value.message_dict

    def test_both_margins_are_rejected_by_database(self):
        """Oba narzuty naraz są odrzucane przez bazę."""
        with pytest.raises(IntegrityError):
            Category.objects.create(
                name="Obrączki",
                margin_percent=Decimal("35.00"),
                margin_amount=15000,
            )
