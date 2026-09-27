"""Wybór promocji dla pozycji koszyka (`CONTEXT.md`, Promotion; ADR 0022, 0023)."""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.accounts.models import MembershipLevel
from apps.orders.models import OrderStatus
from apps.orders.services import cart_items
from apps.promotions.models import PromotionKind
from apps.promotions.services import best_promotions
from apps.products.services.metal_rate import activate_rate
from common.money import Money
from tests.factories.accounts import ProfileFactory, UserFactory
from tests.factories.categories import CategoryFactory
from tests.factories.collections import CollectionFactory
from tests.factories.orders import (
    CartFactory,
    CartItemFactory,
    GuestOrderFactory,
    OrderFactory,
)
from tests.factories.products import (
    EngravableProductFactory,
    MetalRateFactory,
    ProductVariantFactory,
    PublishedProductFactory,
)
from tests.factories.promotions import PromotionFactory, PromotionRedemptionFactory

# Wariant z fabryki: 3,5 g złota 585 za 1299,00 zł. Przy kursie 100 zł/g
# koszt wariantu (próg) to 350,00 zł, więc na obniżkę zostaje 949,00 zł.
PRICE = 129900
FLOOR = 35000


@pytest.fixture
def active_rate():
    return activate_rate(MetalRateFactory(price_per_gram=10000)).rate


def _line(cart=None, **variant_kwargs):
    variant_kwargs.setdefault("product", PublishedProductFactory())
    variant = ProductVariantFactory(**variant_kwargs)
    return CartItemFactory(cart=cart or CartFactory(), variant=variant)


def _discounts(item, **kwargs):
    items = list(cart_items(item.cart))
    result = best_promotions(items, **kwargs)
    return {pk: (applied.promotion, applied.amount) for pk, applied in result.items()}


@pytest.mark.django_db
@pytest.mark.usefixtures("active_rate")
class TestBestPromotion:
    """Na pozycję działa najwyżej jedna promocja — najkorzystniejsza."""

    def test_percent_promotion_lowers_goods_price(self):
        """10% od 1299,00 zł to 129,90 zł obniżki."""
        item = _line()
        promotion = PromotionFactory(value=10)

        assert _discounts(item) == {item.pk: (promotion, Money(12990))}

    def test_most_favourable_promotion_wins(self):
        """Z dwóch pasujących wygrywa ta, która daje więcej — 200 zł > 129,90 zł."""
        item = _line()
        PromotionFactory(value=10)
        bigger = PromotionFactory(kind=PromotionKind.AMOUNT, value=20000)

        assert _discounts(item) == {item.pk: (bigger, Money(20000))}

    def test_amount_promotion_counts_every_specimen(self):
        """Kwota obniżki dotyczy egzemplarza, więc dwie sztuki to podwójna obniżka."""
        item = _line()
        item.quantity = 2
        item.save()
        promotion = PromotionFactory(kind=PromotionKind.AMOUNT, value=1000)

        assert _discounts(item) == {item.pk: (promotion, Money(2000))}

    def test_engraving_is_not_discounted(self):
        """Grawer to usługa, nie towar — procent liczy się od samego wyrobu."""
        item = _line(product=EngravableProductFactory())
        item.engraving_text = "Na zawsze"
        item.save()
        promotion = PromotionFactory(value=10)

        assert _discounts(item) == {item.pk: (promotion, Money(12990))}


@pytest.mark.django_db
class TestCostFloor:
    """Cena po rabacie nie schodzi poniżej kosztu wariantu (ADR 0022)."""

    def test_discount_is_capped_at_cost(self, active_rate):
        """90% dałoby cenę poniżej kosztu — obniżka kończy się na progu."""
        item = _line()
        promotion = PromotionFactory(value=90)

        assert _discounts(item) == {item.pk: (promotion, Money(PRICE - FLOOR))}

    def test_amount_above_price_is_capped_at_cost(self, active_rate):
        """Kwota 600 zł przy cenie 400 zł i koszcie 350 zł daje tylko 50 zł obniżki."""
        item = _line(price=40000)
        amount = PromotionFactory(kind=PromotionKind.AMOUNT, value=60000)

        assert _discounts(item) == {item.pk: (amount, Money(5000))}

    def test_price_at_cost_gets_nothing(self, active_rate):
        """Wariant sprzedawany po koszcie nie ma już czego obniżać."""
        item = _line(price=FLOOR)
        PromotionFactory(value=10)

        assert _discounts(item) == {}

    def test_without_known_cost_no_promotion_applies(self):
        """Bez aktywnego kursu kosztu nie da się policzyć — promocja nie działa."""
        item = _line()
        PromotionFactory(value=10)

        assert _discounts(item) == {}


@pytest.mark.django_db
@pytest.mark.usefixtures("active_rate")
class TestPromotionConditions:
    """Okres, kod, członkostwo i minimalna wartość koszyka."""

    def test_expired_promotion_does_not_apply(self):
        """Promocja, która się skończyła, nie działa."""
        item = _line()
        PromotionFactory(
            starts_at=timezone.now() - timedelta(days=10),
            ends_at=timezone.now() - timedelta(days=1),
        )

        assert _discounts(item) == {}

    def test_future_promotion_does_not_apply(self):
        """Promocja, która jeszcze się nie zaczęła, nie działa."""
        item = _line()
        PromotionFactory(starts_at=timezone.now() + timedelta(days=1))

        assert _discounts(item) == {}

    def test_code_promotion_needs_its_code(self):
        """Promocja z kodem działa tylko w koszyku, który ten kod aktywował."""
        item = _line()
        promotion = PromotionFactory(code="LATO")

        assert _discounts(item) == {}
        assert _discounts(item, code_promotion=promotion) == {
            item.pk: (promotion, Money(12990))
        }

    def test_premium_promotion_denies_regular_customer(self):
        """Klient bez premium nie dostaje rabatu z promocji z warunkiem członkostwa."""
        user = UserFactory()
        ProfileFactory(user=user)
        item = _line(cart=CartFactory(user=user))
        PromotionFactory(requires_premium=True)

        assert _discounts(item, user=user) == {}

    def test_premium_promotion_denies_guest(self):
        """Gość — bez profilu — nie może być premium."""
        item = _line()
        PromotionFactory(requires_premium=True)

        assert _discounts(item) == {}

    def test_premium_promotion_grants_discount_to_premium_customer(self):
        """Klient premium dostaje rabat z promocji z warunkiem członkostwa."""
        user = UserFactory()
        ProfileFactory(user=user, membership=MembershipLevel.PREMIUM)
        item = _line(cart=CartFactory(user=user))
        promotion = PromotionFactory(requires_premium=True)

        assert _discounts(item, user=user) == {item.pk: (promotion, Money(12990))}

    def test_cart_below_minimum_value_gets_nothing(self):
        """Koszyk za 1299 zł nie spełnia progu 2000 zł."""
        item = _line()
        PromotionFactory(min_cart_value=200000)

        assert _discounts(item) == {}

    def test_cart_at_minimum_value_qualifies(self):
        """Próg liczy się od wartości koszyka przed rabatami, włącznie."""
        item = _line()
        promotion = PromotionFactory(min_cart_value=PRICE)

        assert _discounts(item) == {item.pk: (promotion, Money(12990))}


@pytest.mark.django_db
@pytest.mark.usefixtures("active_rate")
class TestPromotionScope:
    """Zakres: produkty, kolekcje, kategorie z potomkami albo cały katalog."""

    def test_category_covers_its_descendants(self):
        """Promocja na „Pierścionki" obejmuje produkt z „Zaręczynowych"."""
        parent = CategoryFactory(name="Pierścionki")
        child = CategoryFactory(name="Zaręczynowe", parent=parent)
        item = _line(product=PublishedProductFactory(category=child))
        promotion = PromotionFactory(whole_catalog=False)
        promotion.categories.set([parent])

        assert _discounts(item) == {item.pk: (promotion, Money(12990))}

    def test_other_category_is_not_covered(self):
        """Produkt spoza kategorii promocji jej nie dostaje."""
        item = _line()
        promotion = PromotionFactory(whole_catalog=False)
        promotion.categories.set([CategoryFactory()])

        assert _discounts(item) == {}

    def test_product_scope(self):
        """Promocja przypięta do produktu działa na jego wariant."""
        item = _line()
        promotion = PromotionFactory(whole_catalog=False)
        promotion.products.set([item.variant.product])

        assert _discounts(item) == {item.pk: (promotion, Money(12990))}

    def test_collection_scope(self):
        """Promocja na kolekcję działa na produkty tej kolekcji."""
        item = _line()
        collection = CollectionFactory(products=[item.variant.product])
        promotion = PromotionFactory(whole_catalog=False)
        promotion.collections.set([collection])

        assert _discounts(item) == {item.pk: (promotion, Money(12990))}

    def test_empty_scope_covers_nothing(self):
        """Brak zakresu nie znaczy „cały katalog" — promocja nie działa nigdzie."""
        item = _line()
        PromotionFactory(whole_catalog=False)

        assert _discounts(item) == {}


@pytest.mark.django_db
@pytest.mark.usefixtures("active_rate")
class TestPromotionLimits:
    """Limit globalny i limit na klienta liczą się z zastosowań w zamówieniach."""

    def test_global_limit_reached(self):
        """Promocja z limitem 1, już użyta w innym zamówieniu, nie działa."""
        item = _line()
        promotion = PromotionFactory(global_limit=1)
        PromotionRedemptionFactory(promotion=promotion)

        assert _discounts(item) == {}

    def test_cancelled_order_frees_the_limit(self):
        """Zastosowanie w anulowanym zamówieniu nie zużywa limitu."""
        item = _line()
        promotion = PromotionFactory(global_limit=1)
        PromotionRedemptionFactory(
            promotion=promotion, order=OrderFactory(status=OrderStatus.CANCELLED)
        )

        assert _discounts(item) == {item.pk: (promotion, Money(12990))}

    def test_live_use_still_counts_next_to_cancelled_one(self):
        """Anulowane zamówienie nie maskuje użycia w innym, żywym zamówieniu."""
        item = _line()
        promotion = PromotionFactory(global_limit=1)
        PromotionRedemptionFactory(
            promotion=promotion, order=OrderFactory(status=OrderStatus.CANCELLED)
        )
        PromotionRedemptionFactory(promotion=promotion)

        assert _discounts(item) == {}

    def test_per_customer_limit_blocks_the_same_customer(self):
        """Klient, który już raz skorzystał, nie dostaje promocji drugi raz."""
        user = UserFactory()
        item = _line(cart=CartFactory(user=user))
        promotion = PromotionFactory(per_customer_limit=1)
        PromotionRedemptionFactory(promotion=promotion, order=OrderFactory(user=user))

        assert _discounts(item, user=user) == {}

    def test_per_customer_limit_leaves_other_customers(self):
        """Limit na klienta nie blokuje innych klientów."""
        user = UserFactory()
        item = _line(cart=CartFactory(user=user))
        promotion = PromotionFactory(per_customer_limit=1)
        PromotionRedemptionFactory(promotion=promotion)

        assert _discounts(item, user=user) == {item.pk: (promotion, Money(12990))}

    def test_per_customer_limit_counts_guest_by_email(self):
        """Gość jest rozpoznawany po adresie e-mail zamówienia."""
        item = _line()
        promotion = PromotionFactory(per_customer_limit=1)
        PromotionRedemptionFactory(
            promotion=promotion, order=GuestOrderFactory(email="gosc@test.com")
        )

        assert _discounts(item, user=None, email="GOSC@test.com") == {}
