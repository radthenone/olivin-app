from drf_spectacular.utils import (
    OpenApiParameter,
    extend_schema,
    extend_schema_view,
)

from apps.orders.serializers import (
    CartItemQuantitySerializer,
    CartItemWriteSerializer,
    CartSerializer,
    OrderCreateSerializer,
    OrderLookupSerializer,
    OrderSerializer,
    CouponCodeSerializer,
    PromotionCodeSerializer,
    SalesDocumentSerializer,
)
from apps.payments.serializers import PaymentIntentSerializer

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

cart_promotion_code_schema = extend_schema_view(
    post=extend_schema(
        tags=["Cart"],
        summary="Kod promocyjny w koszyku",
        description=(
            "Aktywuje promocję kodową; nowy kod zastępuje poprzedni. Nieznany "
            "albo nieaktywny kod to 400. Czy promocja obniży którąś pozycję, "
            "widać w `discountAmount` — zależy od zakresu, limitów i progu "
            "koszyka. Bez tokenu gość dostaje nowy koszyk i jego token."
        ),
        parameters=[CART_TOKEN_PARAMETER],
        request=PromotionCodeSerializer,
        responses={200: CartSerializer},
    ),
)

cart_coupon_schema = extend_schema_view(
    post=extend_schema(
        tags=["Cart"],
        summary="Kupon w koszyku",
        description=(
            "Wpisuje kupon; nowy kod zastępuje poprzedni. Nieznany, "
            "wykorzystany albo przeterminowany kupon to 400. Kupon pokrywa "
            "towar po promocjach (`couponAmount`), nigdy dostawę; nadwyżka "
            "nominału przepada. Limit żądań zakresu `auth` (10/min). Bez "
            "tokenu gość dostaje nowy koszyk i jego token."
        ),
        parameters=[CART_TOKEN_PARAMETER],
        request=CouponCodeSerializer,
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


order_schema = extend_schema_view(
    list=extend_schema(
        tags=["Orders"],
        summary="Własne zamówienia zalogowanego klienta",
        description=(
            "Historia zamówień wymaga zalogowania. Gość otwiera pojedyncze "
            "zamówienie numerem i adresem e-mail."
        ),
        responses={200: OrderSerializer(many=True)},
    ),
    retrieve=extend_schema(
        tags=["Orders"],
        summary="Zamówienie po numerze",
        description=(
            "Zalogowany klient widzi wyłącznie własne zamówienia. Gość podaje "
            "dodatkowo `email` — sam numer zamówienia go nie otwiera."
        ),
        parameters=[OrderLookupSerializer],
        responses={200: OrderSerializer},
    ),
    create=extend_schema(
        tags=["Orders"],
        summary="Złożenie zamówienia z koszyka",
        description=(
            "Zamówienie powstaje w statusie `pending` z kopią cen, kosztu "
            "dostawy i grawerunku, zakłada rezerwacje stanu i czyści koszyk. "
            "Wymaga akceptacji bieżącej wersji regulaminu; gość ponad "
            "10 000 zł jest odrzucany."
        ),
        parameters=[CART_TOKEN_PARAMETER],
        request=OrderCreateSerializer,
        responses={201: OrderSerializer},
    ),
    cancel=extend_schema(
        tags=["Orders"],
        summary="Anulowanie zamówienia",
        description=(
            "Zamówienie `pending` jest anulowane od razu i zwalnia rezerwacje "
            "(200). Zamówienie `paid` zleca zwrot u operatora i odpowiada 202 "
            "w statusie `paid` — do `cancelled` przechodzi po zdarzeniu "
            "zwrotu, a towar wraca wtedy na stan. Pozostałe statusy są "
            "odrzucane."
        ),
        parameters=[OrderLookupSerializer],
        request=None,
        responses={200: OrderSerializer, 202: OrderSerializer},
    ),
    payment=extend_schema(
        tags=["Orders"],
        summary="Rozpoczęcie zapłaty za zamówienie",
        description=(
            "Zakłada intencję płatniczą na kwotę do zapłaty z zamówienia "
            "i zwraca `clientSecret` dla arkusza płatności (mobile) albo "
            "elementu (web). Każde wywołanie to nowa próba; rezerwacje stanu "
            "są odnawiane na 30 minut. O zapłacie rozstrzyga wyłącznie "
            "zdarzenie od operatora — status zamówienia trzeba odpytać."
        ),
        parameters=[OrderLookupSerializer],
        request=None,
        responses={201: PaymentIntentSerializer},
    ),
    documents=extend_schema(
        tags=["Orders"],
        summary="Dokumenty sprzedaży zamówienia",
        description=(
            "Potwierdzenie zamówienia i — na prośbę klienta — faktura imienna, "
            "wystawiane raz po opłaceniu zamówienia. Każdy dokument ma adres "
            "PDF podpisany na czas (`S3_SIGNED_URL_TTL`); po wygaśnięciu "
            "trzeba pobrać listę ponownie. Zamówienie tuż po zapłacie może "
            "mieć jeszcze pustą listę — dokumenty powstają w tle."
        ),
        parameters=[OrderLookupSerializer],
        responses={200: SalesDocumentSerializer(many=True)},
    ),
)
