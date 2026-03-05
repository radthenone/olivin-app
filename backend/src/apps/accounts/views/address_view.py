from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import Address
from apps.accounts.schema import address_schema
from apps.accounts.serializers import AddressSerializer

# Create your views here.


@address_schema
class AddressViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing address instances.

    Actions:
    - list:           GET  /api/v1/addresses/
    - retrieve:       GET  /api/v1/addresses/{id}/
    - create:         POST /api/v1/addresses/
    - update:         PUT  /api/v1/addresses/{id}/
    - partial_update: PATCH /api/v1/addresses/{id}/
    - destroy:        DELETE /api/v1/addresses/{id}/
    - set_default:    PATCH /api/v1/addresses/{id}/set-default/
    """

    permission_classes = [IsAuthenticated]
    serializer_class = AddressSerializer

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["patch"], url_path="set-default")
    def set_default(self, request, pk=None):
        Address.objects.filter(user=request.user).update(is_default=False)
        address = self.get_object()
        if address.is_default:
            raise ValidationError("Address is already set as default")
        address.is_default = True
        address.save()
        return Response(self.get_serializer(address).data, status=status.HTTP_200_OK)
