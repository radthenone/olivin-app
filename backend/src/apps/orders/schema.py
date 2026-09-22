from drf_spectacular.utils import (
    OpenApiParameter,
    extend_schema,
    extend_schema_view,
)

from apps.orders.serializers import (
    CartItemQuantitySerializer,
    CartItemWriteSerializer,
    CartSerializer,
)

CART_TOKEN_PARAMETER = OpenApiParameter(
    name="X-Cart-Token",
    type=str,
    location=OpenApiParameter.HEADER,
    required=False,
    description=(
        "Token koszyka gościa wydany przy pierwszym dodaniu pozycji. "
        "Zalogowany klient go nie wysyła — koszyk wynika z uwierzytelnienia."
    ),
)

cart_schema = extend_schema_view(
    get=extend_schema(
        tags=["Cart"],
        summary="Koszyk klienta albo gościa",
        description=(
            "Pozycje z ceną aktualną (koszyk nie zamraża cen), cena "
            "grawerunku osobno, liczba pozycji i suma. Klient bez koszyka "
            "dostaje pusty koszyk, a nie 404 — odczyt nie zakłada wiersza."
        ),
        parameters=[CART_TOKEN_PARAMETER],
        responses={200: CartSerializer},
    ),
)

cart_merge_schema = extend_schema_view(
    post=extend_schema(
        tags=["Cart"],
        summary="Scalenie koszyka gościa z koszykiem konta",
        description=(
            "Pozycje gościa trafiają do koszyka konta: te o tej samej "
            "personalizacji sumują ilości w granicach limitu sztuk, "
            "pozostałe stają obok. Koszyk gościa i jego token przestają "
            "istnieć."
        ),
        parameters=[CART_TOKEN_PARAMETER],
        request=None,
        responses={200: CartSerializer},
    ),
)

cart_item_schema = extend_schema_view(
    create=extend_schema(
        tags=["Cart"],
        summary="Dodanie pozycji do koszyka",
        description=(
            "Żądanie bez tokenu zakłada koszyk gościa i zwraca jego token "
            "w polu `cartToken`. Pozycja o tej samej personalizacji dolicza "
            "sztuki; inny grawerunek zakłada osobną pozycję."
        ),
        parameters=[CART_TOKEN_PARAMETER],
        request=CartItemWriteSerializer,
        responses={201: CartSerializer},
    ),
    partial_update=extend_schema(
        tags=["Cart"],
        summary="Zmiana liczby sztuk pozycji",
        description="Zero usuwa pozycję z koszyka.",
        parameters=[CART_TOKEN_PARAMETER],
        request=CartItemQuantitySerializer,
        responses={200: CartSerializer},
    ),
    destroy=extend_schema(
        tags=["Cart"],
        summary="Usunięcie pozycji z koszyka",
        parameters=[CART_TOKEN_PARAMETER],
        responses={200: CartSerializer},
    ),
)
