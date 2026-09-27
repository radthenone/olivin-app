from drf_spectacular.utils import extend_schema, extend_schema_view

from apps.consents.serializers import ConsentDocumentSerializer, ConsentSerializer

consent_document_schema = extend_schema_view(
    list=extend_schema(
        tags=["Consents"],
        summary="Bieżące wersje dokumentów",
        description=(
            "Po jednej obowiązującej wersji regulaminu, polityki prywatności "
            "i zgody marketingowej. Rodzaj bez dokumentu jest pominięty."
        ),
        responses={200: ConsentDocumentSerializer(many=True)},
    ),
)

consent_schema = extend_schema_view(
    create=extend_schema(
        tags=["Consents"],
        summary="Zapis zgody",
        description=(
            "Zalogowany klient udziela zgody na konto, gość — na podany e-mail. "
            "Dokument musi być bieżącą wersją z `GET /consents/documents/`."
        ),
        request=ConsentSerializer,
        responses={201: ConsentSerializer},
    ),
)
