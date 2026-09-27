from drf_spectacular.utils import extend_schema, extend_schema_view

from apps.payments.serializers import WebhookAckSerializer

webhook_schema = extend_schema_view(
    post=extend_schema(
        tags=["Payments"],
        summary="Zdarzenie od operatora płatności",
        description=(
            "Wywoływane przez operatora, nie przez aplikację. Podpis zdarzenia "
            "jest weryfikowany; to samo zdarzenie dostarczone ponownie "
            "zwraca `processed: false` i niczego nie zmienia."
        ),
        request=None,
        responses={200: WebhookAckSerializer},
    ),
)
