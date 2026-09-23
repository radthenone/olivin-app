from __future__ import annotations

from factory.declarations import LazyFunction, SubFactory
from factory.django import DjangoModelFactory

from apps.orders.models import Cart, CartItem, Order, OrderItem, OrderStatus
from apps.orders.services.cart import new_guest_token
from tests.factories.accounts import UserFactory
from tests.factories.consents import ConsentDocumentFactory
from tests.factories.products import ProductVariantFactory
from tests.factories.shipping import ShippingMethodFactory


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


class OrderFactory(DjangoModelFactory):
    """Zamówienie zalogowanego klienta, oczekujące na zapłatę."""

    class Meta:
        model = Order

    user = SubFactory(UserFactory)
    email = "klient@test.com"
    status = OrderStatus.PENDING
    recipient_name = "Jan Kowalski"
    street = "Złota 44"
    street2 = ""
    city = "Warszawa"
    postal_code = "00-120"
    country = "PL"
    shipping_method = SubFactory(ShippingMethodFactory)
    shipping_method_name = "Kurier"
    shipping_cost = 1990
    currency = "PLN"
    terms_document = SubFactory(ConsentDocumentFactory)


class GuestOrderFactory(DjangoModelFactory):
    """Zamówienie gościa — bez konta, odnajdywane numerem i adresem.

    Osobna fabryka, nie podklasa `OrderFactory`: nadpisanie `SubFactory`
    wartością `None` nie przechodzi kontroli typów (patrz `GuestCartFactory`).
    """

    class Meta:
        model = Order

    user = None
    email = "gosc@test.com"
    status = OrderStatus.PENDING
    recipient_name = "Jan Kowalski"
    street = "Złota 44"
    street2 = ""
    city = "Warszawa"
    postal_code = "00-120"
    country = "PL"
    shipping_method = SubFactory(ShippingMethodFactory)
    shipping_method_name = "Kurier"
    shipping_cost = 1990
    currency = "PLN"
    terms_document = SubFactory(ConsentDocumentFactory)


class OrderItemFactory(DjangoModelFactory):
    """Pozycja zamówienia z kopią danych wariantu (ADR 0010)."""

    class Meta:
        model = OrderItem

    order = SubFactory(OrderFactory)
    variant = SubFactory(ProductVariantFactory)
    product_name = "Pierścionek"
    sku = "SKU-TEST"
    is_made_to_order = False
    quantity = 1
    unit_price = 100000
    vat_rate = "0.2300"
    is_vat_exempt = False
    vat_exemption_basis = ""
    engraving_text = ""
    engraving_price = 0
    size = ""
    second_size = ""
    second_engraving_text = ""
