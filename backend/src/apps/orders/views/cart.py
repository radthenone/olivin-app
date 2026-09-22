from __future__ import annotations

from dataclasses import dataclass

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from django.http import HttpRequest
from rest_framework.views import APIView

from apps.orders.models import Cart, CartItem
from apps.orders.schema import cart_item_schema, cart_merge_schema, cart_schema
from apps.orders.serializers import (
    CartItemQuantitySerializer,
    CartItemWriteSerializer,
    CartSerializer,
)
from apps.orders.services import (
    add_item,
    cart_items,
    get_cart,
    get_or_create_cart,
    merge_carts,
    remove_item,
    set_quantity,
    totals,
)
from common.money import DEFAULT_CURRENCY, Money

# Gość nosi swój koszyk w tym nagłówku — nie w ciasteczku, bo aplikacja
# mobilna ciasteczek nie ma (ADR 0030).
CART_TOKEN_HEADER = "X-Cart-Token"
_META_KEY = "HTTP_X_CART_TOKEN"


@dataclass(frozen=True, slots=True)
class CartPayload:
    """Koszyk gotowy do serializacji — pozycje, token i podsumowanie razem."""

    cart_token: str | None
    items: list[CartItem]
    item_count: int
    subtotal: Money
    discount_amount: Money
    coupon_amount: Money
    total: Money


def _empty_view() -> CartPayload:
    """Klient bez koszyka widzi pusty koszyk, nie 404.

    Odczyt nie zakłada wiersza: koszyk powstaje dopiero przy pierwszym
    dodaniu pozycji, inaczej każdy robot indeksujący zostawiałby po sobie
    pusty koszyk do posprzątania.
    """
    zero = Money.zero(DEFAULT_CURRENCY)
    return CartPayload(
        cart_token=None,
        items=[],
        item_count=0,
        subtotal=zero,
        discount_amount=zero,
        coupon_amount=zero,
        total=zero,
    )


def _view_of(cart: Cart) -> CartPayload:
    summary = totals(cart)
    return CartPayload(
        cart_token=cart.session_key or None,
        items=list(cart_items(cart)),
        item_count=summary.item_count,
        subtotal=summary.subtotal,
        discount_amount=summary.discount_amount,
        coupon_amount=summary.coupon_amount,
        total=summary.total,
    )


def _token(request: Request | HttpRequest) -> str | None:
    return request.META.get(_META_KEY) or None


def _user(request: Request | HttpRequest):
    return request.user if request.user.is_authenticated else None


def _as_drf_error(error: DjangoValidationError) -> ValidationError:
    """Odmowa z serwisu ma wyjść jako 400 z polami, nie jako 500."""
    return ValidationError(error.message_dict)


@cart_schema
class CartDetailView(APIView):
    """Pełny widok koszyka.

    Actions:
    - get: GET /cart/ — pozycje z ceną aktualną, liczba pozycji i suma

    Dla każdego: gość ma koszyk, zanim założy konto. Właściciel bierze się
    z uwierzytelnienia albo z nagłówka `X-Cart-Token`, nigdy z treści
    żądania — inaczej dałoby się podejrzeć cudzy koszyk, znając sam
    identyfikator.
    """

    permission_classes = [AllowAny]
    serializer_class = CartSerializer

    def get(self, request: Request) -> Response:
        cart = get_cart(user=_user(request), token=_token(request))
        view = _empty_view() if cart is None else _view_of(cart)
        return Response(CartSerializer(view).data)


@cart_merge_schema
class CartMergeView(APIView):
    """Scalenie koszyka gościa z koszykiem konta.

    Actions:
    - post: POST /cart/merge/ — pozycje gościa trafiają do koszyka konta

    Tylko dla zalogowanego, bo scalać jest z czym dopiero po zalogowaniu.
    Token gościa przestaje działać razem z jego koszykiem (ADR 0030).
    """

    permission_classes = [IsAuthenticated]
    serializer_class = CartSerializer

    def post(self, request: Request) -> Response:
        token = _token(request)
        guest = get_cart(user=None, token=token) if token else None
        if guest is None:
            raise ValidationError(
                {
                    "cart_token": (
                        f"Podaj token koszyka gościa w nagłówku {CART_TOKEN_HEADER}."
                    )
                }
            )

        target = get_or_create_cart(user=request.user)
        merged = merge_carts(guest=guest, target=target)
        return Response(CartSerializer(_view_of(merged)).data)


@cart_item_schema
class CartItemViewSet(viewsets.GenericViewSet):
    """Pozycje koszyka.

    Actions:
    - create:  POST /cart/items/        — dodaje pozycję; gość dostaje token
    - partial_update: PATCH /cart/items/{id}/ — zmienia liczbę sztuk
    - destroy: DELETE /cart/items/{id}/ — usuwa pozycję

    Każda odpowiedź to cały koszyk, nie sama pozycja: po zmianie ilości
    klient i tak potrzebuje nowej sumy, a osobne wywołanie po nią umiałoby
    się rozjechać z tym, co właśnie zapisał.
    """

    permission_classes = [AllowAny]
    serializer_class = CartSerializer
    pagination_class = None
    filter_backends: list = []
    queryset = CartItem.objects.none()

    def get_queryset(self):
        cart = get_cart(user=_user(self.request), token=_token(self.request))
        if cart is None:
            return CartItem.objects.none()
        return CartItem.objects.filter(cart=cart).select_related(
            "variant", "variant__product", "variant__inventory"
        )

    def create(self, request: Request, *args, **kwargs) -> Response:
        payload = CartItemWriteSerializer(data=request.data)
        payload.is_valid(raise_exception=True)

        cart = get_or_create_cart(user=_user(request), token=_token(request))
        try:
            add_item(cart, **payload.validated_data)
        except DjangoValidationError as error:
            raise _as_drf_error(error) from error

        return Response(
            CartSerializer(_view_of(cart)).data, status=status.HTTP_201_CREATED
        )

    def partial_update(self, request: Request, *args, **kwargs) -> Response:
        item = self.get_object()
        payload = CartItemQuantitySerializer(data=request.data)
        payload.is_valid(raise_exception=True)

        try:
            set_quantity(item, payload.validated_data["quantity"])
        except DjangoValidationError as error:
            raise _as_drf_error(error) from error

        return Response(CartSerializer(_view_of(item.cart)).data)

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        item = self.get_object()
        cart = item.cart
        remove_item(item)
        return Response(CartSerializer(_view_of(cart)).data)
