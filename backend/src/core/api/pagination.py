from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """Paginacja numerowana wspólna dla całego API.

    Dwadzieścia cztery pozycje na stronę, bo taka liczba dzieli się bez reszty
    przez dwa, trzy i cztery — czyli przez każdą szerokość siatki katalogu.
    Klient może zażądać innej wielkości przez `?page_size`, ale nie większej
    niż sto: strona liczona w tysiącach pozycji to w praktyce zrzut bazy.
    """

    page_size = 24
    page_size_query_param = "page_size"
    max_page_size = 100
