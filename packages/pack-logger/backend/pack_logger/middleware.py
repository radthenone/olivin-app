"""
Django middleware dla automatycznego logowania API z pełnymi danymi developerskimi.
Obsługuje case conversion (camelCase ↔ snake_case).
"""
import time
import json
from typing import Optional, Dict, Any
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpRequest, HttpResponse, JsonResponse
from .logger import log


class ApiLoggingMiddleware(MiddlewareMixin):
    """
    Middleware do automatycznego logowania requestów z pełnymi danymi.

    Loguje:
    - Headers (z maskowaniem wrażliwych)
    - Query parameters
    - Body (z maskowaniem wrażliwych)
    - Response headers
    - Response body
    - Czas wykonania
    """

    EXCLUDED_PATHS = ['/admin/', '/static/', '/media/', '/favicon.ico', '/api/health/']
    SENSITIVE_HEADERS = {'authorization', 'cookie', 'x-csrftoken', 'x-api-key', 'session'}
    SENSITIVE_BODY_FIELDS = {'password', 'token', 'secret', 'api_key', 'access_token',
                            'refresh_token', 'card_number', 'cvv', 'ssn'}

    def should_log(self, path: str) -> bool:
        """Sprawdza czy ścieżka powinna być logowana."""
        return not any(path.startswith(excluded) for excluded in self.EXCLUDED_PATHS)

    def mask_sensitive_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Maskuje wrażliwe nagłówki."""
        masked = {}
        for key, value in headers.items():
            key_lower = key.lower()
            if any(sensitive in key_lower for sensitive in self.SENSITIVE_HEADERS):
                masked[key] = '***MASKED***'
            else:
                masked[key] = value
        return masked

    def mask_sensitive_body(self, data: Any) -> Any:
        """Maskuje wrażliwe pola w body."""
        if not isinstance(data, dict):
            return data

        masked = {}
        for key, value in data.items():
            key_lower = key.lower()
            if any(sensitive in key_lower for sensitive in self.SENSITIVE_BODY_FIELDS):
                masked[key] = '***MASKED***'
            elif isinstance(value, dict):
                masked[key] = self.mask_sensitive_body(value)
            elif isinstance(value, list):
                masked[key] = [self.mask_sensitive_body(item) if isinstance(item, dict) else item
                              for item in value]
            else:
                masked[key] = value
        return masked

    def get_request_headers(self, request: HttpRequest) -> Dict[str, str]:
        """
        Pobiera nagłówki z requestu (wybrane, przydatne dla developera).

        Args:
            request: HttpRequest

        Returns:
            Dict: Nagłówki
        """
        headers = {}
        useful_headers = [
            'content-type',
            'content-length',
            'user-agent',
            'accept',
            'accept-language',
            'accept-encoding',
            'referer',
            'origin',
            'x-requested-with',
            'x-forwarded-for',
            'x-real-ip',
        ]

        for header_name in useful_headers:
            value = request.headers.get(header_name)
            if value:
                headers[header_name] = value

        # Dodaj wszystkie custom headers (X-*, Authorization, etc.)
        for key, value in request.headers.items():
            if key.startswith('x-') or key.lower() in ['authorization', 'cookie']:
                headers[key] = value

        return self.mask_sensitive_headers(headers)

    def get_request_body(self, request: HttpRequest) -> Optional[Any]:
        """
        Pobiera i parsuje body z requestu.
        Django REST Framework camel-case middleware już przekonwertował camelCase → snake_case.

        Args:
            request: HttpRequest

        Returns:
            Optional[Any]: Sparsowane body lub None
        """
        if not request.body:
            return None

        # Sprawdź content type
        content_type = request.content_type or ''

        if 'application/json' in content_type:
            try:
                body = json.loads(request.body.decode('utf-8'))
                # Body jest już w snake_case dzięki CamelCaseMiddleWare
                return self.mask_sensitive_body(body)
            except (json.JSONDecodeError, UnicodeDecodeError):
                return None
        elif 'application/x-www-form-urlencoded' in content_type:
            # Form data
            return dict(request.POST) if request.POST else None
        elif 'multipart/form-data' in content_type:
            # Multipart - tylko nazwy pól, nie wartości plików
            return {
                'fields': list(request.POST.keys()) if request.POST else [],
                'files': list(request.FILES.keys()) if request.FILES else [],
            }

        return None

    def get_response_headers(self, response: HttpResponse) -> Dict[str, str]:
        """
        Pobiera nagłówki z response (wybrane, przydatne dla developera).

        Args:
            response: HttpResponse

        Returns:
            Dict: Nagłówki
        """
        headers = {}
        useful_headers = [
            'content-type',
            'content-length',
            'x-frame-options',
            'x-content-type-options',
            'cache-control',
            'expires',
        ]

        for header_name in useful_headers:
            value = response.get(header_name)
            if value:
                headers[header_name] = value

        return headers

    def get_response_body(self, response: HttpResponse) -> Optional[Any]:
        """
        Pobiera body z response.
        Django REST Framework camel-case renderer już przekonwertował snake_case → camelCase.

        Args:
            response: HttpResponse

        Returns:
            Optional[Any]: Body response lub None
        """
        if isinstance(response, JsonResponse):
            # JsonResponse ma już sparsowane dane
            try:
                body = json.loads(response.content.decode('utf-8'))
                # Body jest już w camelCase dzięki CamelCaseJSONRenderer
                # Ogranicz rozmiar dla dużych list
                if isinstance(body, list) and len(body) > 10:
                    return {
                        'items_count': len(body),
                        'first_items': body[:3],
                        'message': '[Truncated - too many items]'
                    }
                return body
            except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
                return None
        elif hasattr(response, 'content'):
            content_type = response.get('Content-Type', '')
            if 'application/json' in content_type:
                try:
                    body = json.loads(response.content.decode('utf-8'))
                    # Body jest już w camelCase
                    if isinstance(body, list) and len(body) > 10:
                        return {
                            'items_count': len(body),
                            'first_items': body[:3],
                            'message': '[Truncated - too many items]'
                        }
                    return body
                except (json.JSONDecodeError, UnicodeDecodeError):
                    return None
            elif 'text/html' in content_type:
                return f"[HTML Content - {len(response.content)} bytes]"
            else:
                return f"[Binary Content - {len(response.content)} bytes]"

        return None

    def get_client_ip(self, request: HttpRequest) -> str:
        """Pobiera rzeczywisty IP klienta."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')

    def process_request(self, request: HttpRequest) -> None:
        """Loguje request przed przetworzeniem."""
        if not self.should_log(request.path):
            return

        # Zapisz czas rozpoczęcia
        request._logging_start_time = time.time()

        # Pobierz wszystkie dane
        headers = self.get_request_headers(request)
        query_params = dict(request.GET) if request.GET else None
        body = self.get_request_body(request)
        content_type = request.content_type

        # Loguj z pełnymi danymi
        log.api_request(
            method=request.method,
            path=request.path,
            user=str(request.user) if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous',
            user_id=request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None,
            ip=self.get_client_ip(request),
            headers=headers,
            query_params=query_params,
            body=body,
            content_type=content_type,
        )

    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Loguje response po przetworzeniu."""
        if not self.should_log(request.path):
            return response

        # Oblicz czas wykonania
        duration = 0
        if hasattr(request, '_logging_start_time'):
            duration = (time.time() - request._logging_start_time) * 1000

        # Pobierz dane response
        headers = self.get_response_headers(response)
        body = self.get_response_body(response)

        # Loguj z pełnymi danymi
        log.api_response(
            method=request.method,
            path=request.path,
            status=response.status_code,
            duration_ms=duration,
            headers=headers,
            body=body,
        )

        return response
