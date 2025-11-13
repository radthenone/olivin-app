"""
Uniwersalny system logowania - wersja standalone (bez zapisu do plików).
"""
import json
import logging
from typing import Any, Dict, Optional
from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme


# Globalna konsola Rich
console = Console(theme=Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "red bold",
    "success": "green bold",
}))


class PackLogger:
    """
    Główna klasa loggera - tylko konsola, bez plików.

    Przykład:
        from pack_logger import log
        log.info("User logged in", user_id=123, email="user@example.com")
    """

    def __init__(self, name: str = 'pack', debug: bool = False):
        """
        Inicjalizacja loggera.

        Args:
            name: Nazwa loggera
            debug: Czy włączyć tryb debug
        """
        self.logger = logging.getLogger(name)
        self.debug_mode = debug

        # Konfiguruj handler jeśli jeszcze nie ma
        if not self.logger.handlers:
            console_handler = RichHandler(
                console=console,
                rich_tracebacks=True,
                tracebacks_show_locals=debug,
                show_time=True,
                show_level=True,
                show_path=debug,
            )
            console_handler.setLevel(logging.DEBUG if debug else logging.INFO)
            self.logger.setLevel(logging.DEBUG if debug else logging.INFO)
            self.logger.addHandler(console_handler)

    def _log(self, level: str, message: str, **kwargs):
        """
        Wewnętrzna metoda logowania.

        Args:
            level: Poziom logu (info, warning, error, etc.)
            message: Wiadomość do zalogowania
            **kwargs: Dodatkowe dane do zalogowania
        """
        log_func = getattr(self.logger, level)

        extra_data = {k: v for k, v in kwargs.items() if v is not None}

        if extra_data and self.debug_mode:
            console.print(message, style=level)
            if extra_data:
                try:
                    formatted_data = json.dumps(extra_data, indent=2, ensure_ascii=False, default=str)
                    console.print(formatted_data, style="dim")
                except Exception:
                    console.print(str(extra_data), style="dim")

        log_func(message, extra={'extra_data': extra_data})

    def debug(self, message: str, **kwargs):
        """Debug log."""
        self._log('debug', message, **kwargs)

    def info(self, message: str, **kwargs):
        """Info log."""
        self._log('info', message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Warning log."""
        self._log('warning', message, **kwargs)

    def error(self, message: str, **kwargs):
        """Error log."""
        self._log('error', message, **kwargs)

    def success(self, message: str, **kwargs):
        """Success log."""
        self._log('info', message, **kwargs)

    def api_request(
        self,
        method: str,
        path: str,
        user: Optional[str] = None,
        ip: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None,
        query_params: Optional[Dict[str, Any]] = None,
        body: Optional[Any] = None,
        content_type: Optional[str] = None,
        **kwargs
    ):
        """
        Loguje API request z pełnymi danymi developerskimi.

        Args:
            method: Metoda HTTP (GET, POST, etc.)
            path: Ścieżka requestu
            user: Użytkownik (opcjonalnie)
            ip: Adres IP klienta (opcjonalnie)
            headers: Nagłówki HTTP (opcjonalnie)
            query_params: Query parameters (opcjonalnie)
            body: Body requestu (opcjonalnie)
            content_type: Content-Type (opcjonalnie)
            **kwargs: Dodatkowe dane
        """
        request_data = {
            'method': method,
            'path': path,
            'user': user,
            'ip': ip,
        }

        if headers:
            request_data['headers'] = headers
        if query_params:
            request_data['query_params'] = query_params
        if body is not None:
            request_data['body'] = body
        if content_type:
            request_data['content_type'] = content_type

        request_data.update(kwargs)

        self._log(
            'info',
            f"API Request: {method} {path}",
            **request_data
        )

    def api_response(
        self,
        method: str,
        path: str,
        status: int,
        duration_ms: float,
        headers: Optional[Dict[str, Any]] = None,
        body: Optional[Any] = None,
        **kwargs
    ):
        """
        Loguje API response z pełnymi danymi developerskimi.

        Args:
            method: Metoda HTTP
            path: Ścieżka requestu
            status: Status code
            duration_ms: Czas wykonania w ms
            headers: Nagłówki response (opcjonalnie)
            body: Body response (opcjonalnie)
            **kwargs: Dodatkowe dane
        """
        level = 'info' if status < 400 else 'error' if status >= 500 else 'warning'

        response_data = {
            'method': method,
            'path': path,
            'status': status,
            'duration_ms': round(duration_ms, 2),
        }

        if headers:
            response_data['headers'] = headers
        if body is not None:
            response_data['body'] = body

        response_data.update(kwargs)

        self._log(
            level,
            f"API Response: {method} {path} [{status}] {duration_ms:.2f}ms",
            **response_data
        )


def configure_logging(debug: bool = False, app_name: str = 'pack') -> Dict[str, Any]:
    """
    Konfiguruje logging dla aplikacji (tylko konsola, bez plików).

    Args:
        debug: Czy włączyć tryb debug
        app_name: Nazwa aplikacji

    Returns:
        Dict: Konfiguracja logowania dla Django LOGGING
    """
    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'rich': {
                '()': 'rich.logging.RichHandler',
                'show_time': True,
                'show_level': True,
                'show_path': debug,
                'rich_tracebacks': True,
                'tracebacks_show_locals': debug,
            },
        },
        'handlers': {
            'console': {
                'class': 'rich.logging.RichHandler',
                'level': 'DEBUG' if debug else 'INFO',
                'formatter': 'rich',
            },
        },
        'loggers': {
            app_name: {
                'level': 'DEBUG' if debug else 'INFO',
                'handlers': ['console'],
                'propagate': False,
            },
            'django': {
                'level': 'INFO',
                'handlers': ['console'],
                'propagate': False,
            },
            'django.request': {
                'level': 'ERROR',
                'handlers': ['console'],
                'propagate': False,
            },
        },
        'root': {
            'level': 'INFO',
            'handlers': ['console'],
        },
    }


# Globalna instancja
log = PackLogger()