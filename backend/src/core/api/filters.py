from rest_framework import filters


class SearchFilter(filters.SearchFilter):
    """`SearchFilter`, który nie ogłasza parametru, którego widok nie obsługuje.

    Backend filtrów jest globalny, ale wyszukiwanie ma sens wyłącznie tam, gdzie
    widok wskazał `search_fields`. Bez tej nadpisanej metody `?search=` trafia do
    schematu każdego endpointu listy, klient generuje dla niego typ, a żądanie
    z tym parametrem cicho zwraca listę niefiltrowaną.
    """

    def get_schema_operation_parameters(self, view):
        if not getattr(view, "search_fields", None):
            return []
        return super().get_schema_operation_parameters(view)
