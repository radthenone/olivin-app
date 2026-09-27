from __future__ import annotations

from factory.declarations import Sequence, SubFactory  # noqa: F401
from factory.django import DjangoModelFactory

from apps.categories.models import Category


class CategoryFactory(DjangoModelFactory):
    """Fabryka dla modelu Category.

    Slug jest wyliczany, więc nie ustawiamy go tu z nazwy — model dopisze
    przyrostek przy kolizji, a testy sprawdzają to osobno.
    """

    class Meta:
        model = Category

    name = Sequence(lambda n: f"Kategoria {n}")
    parent = None
