"""Konwencje warstwy API wspólne dla wszystkich aplikacji domenowych.

Paginacja, filtry i limity żądań są ustawione globalnie w `REST_FRAMEWORK`,
żeby widoki katalogu nie powtarzały tej konfiguracji u siebie.
"""

from core.api.pagination import StandardPagination

__all__ = ["StandardPagination"]
