from __future__ import annotations

from django.db import IntegrityError, transaction
from django.db.models import QuerySet

from apps.accounts.models import CustomUser
from apps.favorites.models import Favorite
from apps.products.models import Product, ProductStatus


def favorites_for(user: CustomUser) -> QuerySet[Favorite]:
    """Ulubione klienta widoczne w API — produkt nieopublikowany znika stąd,
    choć rekord zostaje (`CONTEXT.md`, Favorite)."""
    return (
        Favorite.objects.filter(user=user, product__status=ProductStatus.PUBLISHED)
        .select_related("product")
        .prefetch_related("product__translations")
    )


def add_favorite(*, user: CustomUser, product: Product) -> Favorite:
    """Dodaje produkt do ulubionych; powtórzenie jest bezpieczne (idempotentne).

    `get_or_create` nie zamyka wyścigu dwóch równoległych żądań — oba mogą
    nie znaleźć wiersza, zanim któreś go zapisze. Ograniczenie unikalności
    w bazie jest ostatnią linią obrony: `IntegrityError` z niego oznacza,
    że druga transakcja właśnie wygrała, więc czytamy jej wynik zamiast
    wywracać żądanie.
    """
    try:
        with transaction.atomic():
            favorite, _ = Favorite.objects.get_or_create(user=user, product=product)
    except IntegrityError:
        favorite = Favorite.objects.get(user=user, product=product)
    return favorite


def remove_favorite(*, user: CustomUser, product_slug: str) -> None:
    """Usuwa produkt z ulubionych; brak dopasowania też jest sukcesem (idempotentne)."""
    Favorite.objects.filter(user=user, product__slug=product_slug).delete()


def merge_favorites(
    *, user: CustomUser, product_slugs: list[str]
) -> QuerySet[Favorite]:
    """Scala listę gościa (identyfikatory produktów) z listą konta.

    Nieistniejące i nieopublikowane identyfikatory są pomijane. `bulk_create`
    z `ignore_conflicts=True` zamiast pętli `get_or_create` — jedno zapytanie
    zamiast jednego na pozycję, a ograniczenie unikalności w bazie samo
    odrzuca produkty już ulubione, więc scalenie jest idempotentne. Duplikaty
    w liście gościa są odsiewane przed zapytaniem — inaczej `IN (...)` rośnie
    bez powodu, skoro slug jest unikalny.
    """
    products = Product.objects.published().filter(slug__in=set(product_slugs))
    Favorite.objects.bulk_create(
        [Favorite(user=user, product=product) for product in products],
        ignore_conflicts=True,
    )
    return favorites_for(user)
