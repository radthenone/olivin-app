from drf_spectacular.utils import (OpenApiExample, OpenApiResponse,
                                   extend_schema)

from apps.accounts.serializers import AddressSerializer

set_default_schema=extend_schema(
    summary="Set Default Address",
    description="Sets the address as the default address for the authenticated user.",
    responses={
        200: OpenApiResponse(
            response=AddressSerializer,
            description="Address set as default successfully",
            examples=[
                OpenApiExample(
                    name="Address set as default",
                    value={
                        "id": 1,
                        "street": "ul. Przykładowa 1",
                        "city": "Warszawa",
                        "postal_code": "00-001",
                        "country": "PL",
                        "is_default": True,
                    },
                ),
            ],
        ),
        400: OpenApiResponse(description="Address is already set as default"),
        403: OpenApiResponse(description="Permission denied"),
        404: OpenApiResponse(description="Address not found"),
    },
)