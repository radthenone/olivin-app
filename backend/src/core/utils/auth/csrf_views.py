from django.middleware.csrf import get_token
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@extend_schema_view(
    list=extend_schema(
        tags=["Csrf"],
        responses={
            200: {"type": "object", "properties": {"csrfToken": {"type": "string"}}}
        },
    ),
)
class CsrfViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    def list(self, request):
        return Response(
            {
                "csrfToken": get_token(request),
            },
            status=status.HTTP_200_OK,
        )
