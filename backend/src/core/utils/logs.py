from django.conf import settings
from django.http import JsonResponse
from core.paths import BASE_DIR

def view_logs(request):
    """
    Endpoint do podglądu logów (tylko w development).

    Returns:
        JsonResponse: Ostatnie 100 linii logów z pliku django.log
    """
    if not settings.DEBUG:
        return JsonResponse({"error": "Logs are only available in development mode."}, status=403)

    log_file = BASE_DIR / "logs" / "django.log"

    if not log_file.exists():
        return JsonResponse({
            'logs': [],
            'total_lines': 0,
            'message': 'Log file not found.'
        }, status=404)

    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # Ostatnie 100 linii
            last_lines = lines[-100:] if len(lines) > 100 else lines

        return JsonResponse({
            'logs': [line.rstrip('\n') for line in last_lines],
            'total_lines': len(lines),
            'showing': len(last_lines)
        })
    except Exception as e:
        return JsonResponse({
            'error': f'Error reading log file: {str(e)}'
        }, status=500)