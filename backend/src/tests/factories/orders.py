from __future__ import annotations

from factory.declarations import LazyFunction, SubFactory
from factory.django import DjangoModelFactory

from apps.orders.models import Cart, CartItem
from apps.orders.services.cart import new_guest_token
from tests.factories.accounts import UserFactory
from tests.factories.products import ProductVariantFactory


class CartFactory(DjangoModelFactory):
    """Koszyk zalogowanego klienta."""

    class Meta:
        model = Cart

    user = SubFactory(UserFactory)
    session_key = ""


class GuestCartFactory(DjangoModelFactory):
    """Koszyk gościa — po tokenie, bez konta.

    Osobna fabryka, nie podklasa `CartFactory`: nadpisanie `SubFactory`
    wartością `None` nie przechodzi kontroli typów (patrz `GuestConsentFactory`).
    """

    class Meta:
        model = Cart

    user = None
    session_key = LazyFunction(new_guest_token)


class CartItemFactory(DjangoModelFactory):
    """Pozycja koszyka: jeden wariant, jedna sztuka, bez grawerunku."""

    class Meta:
        model = CartItem

    cart = SubFactory(CartFactory)
    variant = SubFactory(ProductVariantFactory)
    quantity = 1
    engraving_text = ""
    second_size = ""
    second_engraving_text = ""
