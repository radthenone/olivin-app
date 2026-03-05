from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)

from apps.accounts.serializers import ProfileSerializer

profile_schema = extend_schema_view(
    list=extend_schema(tags=["Profiles"]),
    retrieve=extend_schema(tags=["Profiles"]),
    create=extend_schema(tags=["Profiles"]),
    update=extend_schema(tags=["Profiles"]),
    partial_update=extend_schema(tags=["Profiles"]),
    destroy=extend_schema(tags=["Profiles"]),
    change_role=extend_schema(
        tags=["Profiles"],
        summary="Change User Role",
        description="Toggles user role between CUSTOMER and ADMIN.",
        responses={
            200: OpenApiResponse(
                response=ProfileSerializer,
                description="Role changed successfully",
                examples=[
                    OpenApiExample(
                        name="Role changed to ADMIN",
                        value={
                            "email": "user@example.com",
                            "first_name": "John",
                            "last_name": "Doe",
                            "full_name": "John Doe",
                            "date_of_birth": "1990-01-01",
                            "age": 36,
                            "phone_number": "+48123456789",
                            "role": "ADMIN",
                        },
                    ),
                ],
            ),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Profile not found"),
        },
    ),
)
