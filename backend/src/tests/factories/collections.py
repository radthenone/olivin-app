from __future__ import annotations

from factory.declarations import Sequence
from factory.django import DjangoModelFactory
from factory.helpers import post_generation

from apps.collections.models import Collection


class CollectionFactory(DjangoModelFactory):
    """Fabryka dla modelu Collection.

    Produkty przypinamy po zapisie, bo relacja wiele-do-wielu potrzebuje
    istniejącego klucza głównego po obu stronach.
    """

    class Meta:
        model = Collection
        skip_postgeneration_save = True

    name = Sequence(lambda n: f"Kolekcja {n}")
    description = "Opis kampanii"

    @post_generation
    def products(self, create: bool, extracted, **kwargs) -> None:
        # `self` to instancja modelu, nie deklaracja — stuby factory_boy
        # widzą tu jeszcze obiekt `PostGeneration`.
        if create and extracted:
            self.products.set(extracted)  # type: ignore[missing-attribute]
