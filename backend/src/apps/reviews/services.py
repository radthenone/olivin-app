from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import QuerySet

from apps.accounts.models import CustomUser
from apps.orders.models import OrderStatus
from apps.products.models import Product
from apps.reviews.models import Review

DUPLICATE_REVIEW_MESSAGE = "Ten produkt został już oceniony."


def deliverable_products(user: CustomUser) -> QuerySet[Product]:
    """Produkty z dostarczonych zamówień klienta — podstawa prawa do opinii."""
    return Product.objects.filter(
        variants__order_items__order__user=user,
        variants__order_items__order__status=OrderStatus.DELIVERED,
    ).distinct()


def products_to_review(user: CustomUser) -> QuerySet[Product]:
    """Dostarczone produkty, których klient jeszcze nie ocenił.

    `prefetch_related("translations")`: serializer czyta tłumaczoną nazwę
    każdego produktu (`TranslatedCharField`) — bez prefetchu to jedno
    zapytanie na produkt, zamiast jednego na całą listę.
    """
    reviewed = Review.objects.filter(user=user).values_list("product_id", flat=True)
    return (
        deliverable_products(user)
        .exclude(pk__in=reviewed)
        .prefetch_related("translations")
    )


def _reject_ineligible(user: CustomUser, product: Product) -> None:
    if not deliverable_products(user).filter(pk=product.pk).exists():
        raise ValidationError(
            "Opinię można wystawić wyłącznie do produktu z dostarczonego zamówienia."
        )


def create_review(
    *, user: CustomUser, product: Product, rating: int, comment: str
) -> Review:
    """Zakłada opinię — po sprawdzeniu uprawnienia i unikalności.

    Sprawdzenie `exists()` przed zapisem nie zamyka wyścigu: dwa równoległe
    żądania mogą je obie przejść, zanim którekolwiek zapisze wiersz. Ostatnią
    linią obrony jest ograniczenie bazy — `IntegrityError` z niego zamienia
    się w ten sam błąd walidacji, żeby klient dostał 400, nie 500.
    """
    _reject_ineligible(user, product)
    if Review.objects.filter(user=user, product=product).exists():
        raise ValidationError(DUPLICATE_REVIEW_MESSAGE)
    review = Review(user=user, product=product, rating=rating, comment=comment)
    review.full_clean()
    try:
        with transaction.atomic():
            review.save()
    except IntegrityError as error:
        raise ValidationError(DUPLICATE_REVIEW_MESSAGE) from error
    return review


def update_review(review: Review, *, rating: int, comment: str) -> Review:
    """Edycja własnej opinii — zawsze wraca do moderacji."""
    review.rating = rating
    review.comment = comment
    review.restart_moderation()
    review.full_clean()
    review.save()
    return review
