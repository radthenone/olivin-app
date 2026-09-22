from __future__ import annotations

from rest_framework import mixins, viewsets
from rest_framework.permissions import AllowAny

from apps.consents.models import Consent, ConsentDocument
from apps.consents.schema import consent_document_schema, consent_schema
from apps.consents.serializers import ConsentDocumentSerializer, ConsentSerializer


@consent_document_schema
class ConsentDocumentViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Bieżące wersje dokumentów do akceptacji.

    Actions:
    - list: GET /consents/documents/ — po jednej obowiązującej wersji na rodzaj

    Dla każdego: gość musi zobaczyć regulamin przed złożeniem zamówienia,
    zanim ma jakiekolwiek konto. Bez stronicowania — rodzajów są trzy.
    """

    permission_classes = [AllowAny]
    serializer_class = ConsentDocumentSerializer
    pagination_class = None

    def get_queryset(self):
        return ConsentDocument.objects.current_for_all_kinds()


@consent_schema
class ConsentViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """Zapis zgody klienta albo gościa.

    Actions:
    - create: POST /consents/ — zgoda zalogowanego (konto) albo gościa (e-mail)

    Dla każdego, bo gość udziela zgody przed założeniem konta. Tylko zapis:
    rejestr zgód ogląda panel, nie klient.
    """

    permission_classes = [AllowAny]
    serializer_class = ConsentSerializer
    queryset = Consent.objects.none()
