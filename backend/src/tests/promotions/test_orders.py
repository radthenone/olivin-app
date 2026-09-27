"""Promocje w zamówieniu: rabat na pozycji, zastosowania i limity (ADR 0023)."""

from __future__ import annotations

import pytest

from apps.consents.models import ConsentDocument, ConsentKind
from apps.orders.services import (
    CartError,
    ShippingAddress,
    add_item,
    apply_promotion_code,
    create_order,
    merge_carts,
)
from apps.products.services.metal_rate import activate_rate
from apps.promotions.models import PromotionRedemption
from common.money import Money
from tests.factories.accounts import UserFactory
from tests.factories.consents import (
    ConsentDocumentFactory,
    ConsentFactory,
    GuestConsentFactory,
)
from tests.factories.orders import CartFactory, GuestCartFactory, GuestOrderFactory
from tests.factories.products import (
    MetalRateFactory,
    ProductVariantFactory,
    PublishedProductFactory,
    stock,
)
from tests.factories.promotions import PromotionFactory, PromotionRedemptionFactory
from tests.factories.shipping import ShippingMethodFactory

ADDRESS = ShippingAddress(
    recipient_name="Jan Kowalski",
    street="Złota 44",
    city="Warszawa",
    postal_code="00-120",
    country="PL",
)


@pytest.fixture(autouse=True)
def _no_free_shipping(settings):
    settings.FREE_SHIPPING_THRESHOLD = None


@pytest.fixture(autouse=True)
def _active_rate():
    activate_rate(MetalRateFactory(price_per_gram=10000))


def _cart_with_variant(cart, quantity: int = 1):
    variant = ProductVariantFactory(product=PublishedProductFactory(), price=100000)
    stock(variant, 5)
    add_item(cart, variant=variant, quantity=quantity)
    return variant


def _order(cart, *, user=None, email: str = ""):
    return create_order(
        cart=cart,
        address=ADDRESS,
        shipping_method=ShippingMethodFactory(rate=1990),
        user=user,
        email=email,
    )


@pytest.fixture(autouse=True)
def terms():
    return ConsentDocumentFactory(kind=ConsentKind.TERMS)


def _user_with_terms():
    user = UserFactory()
    ConsentFactory(
        user=user, document=ConsentDocument.objects.current(ConsentKind.TERMS)
    )
    return user


@pytest.mark.django_db
class TestOrderWithPromotion:
    """Złożenie zamówienia zamraża rabat promocji."""

    def test_item_and_order_carry_the_discount(self):
        """10% od 2 × 1000 zł: 200 zł na pozycji i w zamówieniu; do zapłaty 1819,90 zł."""
        user = _user_with_terms()
        cart = CartFactory(user=user)
        _cart_with_variant(cart, quantity=2)
        PromotionFactory(value=10)

        order = _order(cart, user=user)

        item = order.items.get()  # type: ignore[missing-attribute]
        assert item.discount_amount == 20000
        assert item.discounted_total == Money(180000)
        assert order.discount_amount == 20000
        assert order.total == Money(181990)

    def test_redemption_is_recorded_with_amount(self):
        """Zastosowanie promocji zapisuje kwotę rabatu tej promocji."""
        user = _user_with_terms()
        cart = CartFactory(user=user)
        _cart_with_variant(cart)
        promotion = PromotionFactory(value=10)

        order = _order(cart, user=user)

        redemption = PromotionRedemption.objects.get(order=order)
        assert redemption.promotion == promotion
        assert redemption.amount == 10000

    def test_order_without_promotion_has_no_redemption(self):
        """Bez promocji nie ma rabatu ani wiersza zastosowania."""
        user = _user_with_terms()
        cart = CartFactory(user=user)
        _cart_with_variant(cart)

        order = _order(cart, user=user)

        assert order.discount_amount == 0
        assert not PromotionRedemption.objects.filter(order=order).exists()

    def test_code_is_used_and_cleared(self):
        """Kod z koszyka daje rabat w zamówieniu, a nowy koszyk zaczyna bez niego."""
        user = _user_with_terms()
        cart = CartFactory(user=user)
        _cart_with_variant(cart)
        PromotionFactory(code="LATO", value=20)
        apply_promotion_code(cart, "lato")

        order = _order(cart, user=user)

        cart.refresh_from_db()
        assert order.discount_amount == 20000
        assert cart.promotion is None

    def test_guest_per_customer_limit_is_checked_by_email(self, terms):
        """Gość, który już skorzystał, nie dostaje rabatu ponownie — rozpoznany po adresie."""
        email = "gosc@test.com"
        GuestConsentFactory(email=email, document=terms)
        promotion = PromotionFactory(per_customer_limit=1)
        # Wcześniejsze zamówienie na ten sam regulamin: osobny dokument z fabryki
        # miałby tę samą datę obowiązywania i remis w `current()` losowałby,
        # który regulamin jest bieżący.
        PromotionRedemptionFactory(
            promotion=promotion,
            order=GuestOrderFactory(email=email, terms_document=terms),
        )
        cart = GuestCartFactory()
        _cart_with_variant(cart)

        order = _order(cart, email=email)

        assert order.discount_amount == 0

    def test_global_limit_is_consumed_by_the_order(self):
        """Promocja z limitem 1 działa w pierwszym zamówieniu, w drugim już nie."""
        PromotionFactory(global_limit=1)
        first_user, second_user = _user_with_terms(), _user_with_terms()
        first_cart, second_cart = (
            CartFactory(user=first_user),
            CartFactory(user=second_user),
        )
        _cart_with_variant(first_cart)
        _cart_with_variant(second_cart)

        first = _order(first_cart, user=first_user)
        second = _order(second_cart, user=second_user)

        assert first.discount_amount == 10000
        assert second.discount_amount == 0


@pytest.mark.django_db
class TestPromotionCode:
    """Aktywacja kodu w koszyku."""

    def test_unknown_code_is_rejected(self):
        """Kod, którego nie ma, to odmowa, a nie cichy brak rabatu."""
        with pytest.raises(CartError):
            apply_promotion_code(CartFactory(), "NIEMA")

    def test_guest_code_survives_login(self):
        """Kod wpisany jako gość przechodzi do koszyka konta przy scaleniu."""
        promotion = PromotionFactory(code="LATO")
        guest = GuestCartFactory()
        apply_promotion_code(guest, "LATO")
        target = CartFactory()

        merged = merge_carts(guest=guest, target=target)

        merged.refresh_from_db()
        assert merged.promotion == promotion
