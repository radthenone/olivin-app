from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers

health_schema = extend_schema(
    responses={
        200: inline_serializer(
            name="HealthCheckResponse",
            fields={
                "status": serializers.ChoiceField(choices=["healthy", "unhealthy"]),
                "services": inline_serializer(
                    name="HealthCheckServices",
                    fields={
                        "database": serializers.CharField(),
                        "redis": serializers.CharField(),
                        "storage": serializers.CharField(),
                    },
                ),
            },
        )
    },
    summary="Health check",
    description="Sprawdza stan wszystkich serwisów (DB, Redis, MinIO).",
    tags=["Health"],
)
