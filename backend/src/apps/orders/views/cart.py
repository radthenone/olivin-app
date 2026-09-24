from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from django.http import HttpRequest
from rest_framework.views import APIView

from apps.orders.models import Cart, CartItem
from apps.orders.schema import (
    cart_item_schema,
    cart_merge_schema,
    cart_promotion_code_schema,
    cart_schema,
)
from apps.orders.serializers import (
    CartItemQuantitySerializer,
    CartItemWriteSerializer,
    CartSerializer,
    PromotionCodeSerializer,
)
from apps.orders.services import (
    CartTotals,
    add_item,
    apply_promotion_code,
    cart_items,
    get_cart,
    get_or_create_cart,
    merge_carts,
    promotions_for,
    remove_item,
    set_quantity,
    totals,
)

if TYPE_CHECKING:
    from apps.accounts.models import Customer, CustomUser

# Gość nosi swój koszyk w tym nagłówku — nie w ciasteczku, bo aplikacja
# mobilna ciasteczek nie ma (ADR 0030).
CART_TOKEN_HEADER = "X-Cart-Token"
_META_KEY = "HTTP_X_CART_TOKEN"


@dataclass(frozen=True, slots=True)
class CartPayload:
    """Koszyk gotowy do serializacji: token, pozycje i podsumowanie razem.

    Podsumowanie zostaje osobnym obiektem z serwisu, zamiast być tu
    przepisane pole po polu — jedno miejsce liczy sumy, jedno je pokazuje.
    """

    cart_token: str | None
    items: list[CartItem]
    totals: CartTotals
    promotion_code: str | None = None


def _empty_payload() -> CartPayload:
    """Klient bez koszyka widzi pusty koszyk, nie 404.

    Odczyt nie zakłada wiersza: koszyk powstaje dopiero przy pierwszym
    dodaniu pozycji, inaczej każdy robot indeksujący zostawiałby po sobie
    pusty koszyk do posprzątania.
    """
    return CartPayload(cart_token=None, items=[], totals=totals([]))


def _payload_of(cart: Cart) -> CartPayload:
    """Koszyk z wyceną promocji — tą samą, którą dostanie zamówienie.

    Właściciel bierze się z koszyka, nie z żądania: limit na klienta liczy
    się dla konta, do którego koszyk należy. Gość nie ma tu jeszcze adresu,
    więc jego limit sprawdza dopiero złożenie zamówienia.
    """
    items = list(cart_items(cart))
    discounts = promotions_for(cart, items, user=cart.user)
    return CartPayload(
        cart_token=cart.session_key or None,
        items=items,
        totals=totals(items, discounts),
        promotion_code=cart.promotion.code if cart.promotion else None,
    )


def token_of(request: Request | HttpRequest) -> str | None:
    """Token koszyka gościa z nagłówka; `None`, gdy go nie przysłał."""
    return request.META.get(_META_KEY) or None


def user_of(request: Request | HttpRequest) -> Customer:
    """Zalogowany klient albo `None` — gość nie jest tu błędem.

    Jedyne miejsce, gdzie `AnonymousUser` zamienia się na `None`; serwisy
    dostają już `Customer`. `cast`, bo stuby typują `request.user` jako
    `AbstractBaseUser | AnonymousUser`, a nie jako `AUTH_USER_MODEL`.
    """
    if not request.user.is_authenticated:
        return None
    return cast("CustomUser", request.user)


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
        cart = get_cart(user=user_of(request), token=token_of(request))
        if cart is None:
            return Response(CartSerializer(_empty_payload()).data)

        cart.touch_on_read()
        return Response(CartSerializer(_payload_of(cart)).data)


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
        token = token_of(request)
        guest = get_cart(user=None, token=token) if token else None
        if guest is None:
            raise ValidationError(
                {
                    "cart_token": (
                        f"Podaj token koszyka gościa w nagłówku {CART_TOKEN_HEADER}."
                    )
                }
            )

        target = get_or_create_cart(user=user_of(request))
        merged = merge_carts(guest=guest, target=target)
        return Response(CartSerializer(_payload_of(merged)).data)


@cart_promotion_code_schema
class CartPromotionCodeView(APIView):
    """Kod promocyjny w koszyku.

    Actions:
    - post: POST /cart/promotion-code/ — aktywuje promocję kodową

    Dla każdego, także gościa — kod wpisuje się przed logowaniem. Koszyk
    powstaje, jeśli go jeszcze nie ma, tak jak przy dodaniu pozycji.
    """

    permission_classes = [AllowAny]
    serializer_class = CartSerializer

    def post(self, request: Request) -> Response:
        payload = PromotionCodeSerializer(data=request.data)
        payload.is_valid(raise_exception=True)

        cart = get_or_create_cart(user=user_of(request), token=token_of(request))
        try:
            apply_promotion_code(cart, payload.validated_data["code"])
        except DjangoValidationError as error:
            raise _as_drf_error(error) from error
        return Response(CartSerializer(_payload_of(cart)).data)


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
        cart = get_cart(user=user_of(self.request), token=token_of(self.request))
        if cart is None:
            return CartItem.objects.none()
        return CartItem.objects.filter(cart=cart).select_related(
            "variant", "variant__product", "variant__inventory"
        )

    def create(self, request: Request, *args, **kwargs) -> Response:
        payload = CartItemWriteSerializer(data=request.data)
        payload.is_valid(raise_exception=True)

        cart = get_or_create_cart(user=user_of(request), token=token_of(request))
        try:
            add_item(cart, **payload.validated_data)
        except DjangoValidationError as error:
            raise _as_drf_error(error) from error

        return Response(
            CartSerializer(_payload_of(cart)).data, status=status.HTTP_201_CREATED
        )

    def partial_update(self, request: Request, *args, **kwargs) -> Response:
        item = self.get_object()
        payload = CartItemQuantitySerializer(data=request.data)
        payload.is_valid(raise_exception=True)

        try:
            set_quantity(item, payload.validated_data["quantity"])
        except DjangoValidationError as error:
            raise _as_drf_error(error) from error

        return Response(CartSerializer(_payload_of(item.cart)).data)

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        item = self.get_object()
        cart = item.cart
        remove_item(item)
        return Response(CartSerializer(_payload_of(cart)).data)
