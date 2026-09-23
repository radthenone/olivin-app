from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.payments.schema import webhook_schema
from apps.payments.services import handle_event
from core.integrations.payments import InvalidSignature, get_provider


@webhook_schema
class PaymentWebhookView(APIView):
    """Zdarzenia od operatora płatności (ADR 0012).

    Bez uwierzytelnienia i bez limitu żądań: tożsamość nadawcy potwierdza
    podpis zdarzenia, a limit zatrzymałby ponowienia operatora akurat
    wtedy, gdy są najbardziej potrzebne. Ciało czytane surowe — podpis
    liczy się z dokładnie tych bajtów, które przyszły, a nie z JSON-a po
    ponownym zserializowaniu.
    """

    permission_classes = [AllowAny]
    authentication_classes: list = []
    throttle_classes: list = []

    def post(self, request: Request) -> Response:
        provider = get_provider()
        signature = request.headers.get(provider.signature_header, "")
        try:
            event = provider.verify_signature(request.body, signature)
        except InvalidSignature:
            return Response(
                {"detail": "Nieprawidłowy podpis zdarzenia."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({"processed": handle_event(event)})
