from __future__ import annotations

from datetime import timedelta

from django.utils import timezone
from factory.declarations import LazyFunction, Sequence, SubFactory
from factory.django import DjangoModelFactory

from apps.promotions.models import (
    Coupon,
    CouponSource,
    Promotion,
    PromotionKind,
    PromotionRedemption,
)
from tests.factories.orders import OrderFactory


class PromotionFactory(DjangoModelFactory):
    """Promocja procentowa na cały katalog, trwająca od wczoraj, bez kodu.

    Zakres M2M (produkty, kolekcje, kategorie) przypina się w teście po
    utworzeniu — `promotion.products.set([...])`.
    """

    class Meta:
        model = Promotion

    name = Sequence(lambda n: f"Promocja {n}")
    kind = PromotionKind.PERCENT
    value = 10
    currency = "PLN"
    whole_catalog = True
    starts_at = LazyFunction(lambda: timezone.now() - timedelta(days=1))
    ends_at = None
    code = ""


class PromotionRedemptionFactory(DjangoModelFactory):
    """Zastosowanie promocji w zamówieniu — zużywa limit."""

    class Meta:
        model = PromotionRedemption

    promotion = SubFactory(PromotionFactory)
    order = SubFactory(OrderFactory)
    amount = 1000


class CouponFactory(DjangoModelFactory):
    """Kupon kampanijny na 100 zł, wydany dziś — kod i ważność z modelu."""

    class Meta:
        model = Coupon

    nominal = 10000
    currency = "PLN"
    source = CouponSource.CAMPAIGN
