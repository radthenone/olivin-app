from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers

from apps.accounts.serializers import (
    AccountAnonymisationDetailSerializer,
    AccountAnonymisationSerializer,
)

account_anonymise_schema = extend_schema(
    tags=["Profiles"],
    summary="Usunięcie konta (anonimizacja)",
    description=(
        "Nieodwracalne. Konto z hasłem potwierdza hasłem (`password`), konto "
        "bez hasła — kodem z maila (`code`, patrz `/code/`). 400 przy złym "
        "potwierdzeniu, 409 gdy trwa niedostarczone zamówienie."
    ),
    request=AccountAnonymisationSerializer,
    responses={
        204: OpenApiResponse(description="Konto zanonimizowane, sesja zakończona"),
        400: OpenApiResponse(
            response=inline_serializer(
                name="AccountAnonymisationError",
                fields={
                    "password": serializers.CharField(required=False),
                    "code": serializers.CharField(required=False),
                    "detail": serializers.CharField(required=False),
                },
            ),
            description=(
                "Błędne hasło (`password`), kod (`code`) albo konto obsługi "
                "sklepu (`detail`)"
            ),
        ),
        409: OpenApiResponse(
            response=AccountAnonymisationDetailSerializer,
            description="Trwa niedostarczone zamówienie",
        ),
    },
)

account_anonymise_code_schema = extend_schema(
    tags=["Profiles"],
    summary="Kod potwierdzenia usunięcia konta",
    description=(
        "Tylko dla konta bez hasła (logowanie społecznościowe): wysyła kod "
        "na adres konta, ważny 15 minut. 400 dla konta z hasłem."
    ),
    request=None,
    responses={
        202: AccountAnonymisationDetailSerializer,
        400: OpenApiResponse(
            response=AccountAnonymisationDetailSerializer,
            description="Konto ma hasło — potwierdź hasłem",
        ),
    },
)
