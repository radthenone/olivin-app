from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import Address, Profile
from apps.accounts.schema import address_schema
from apps.accounts.serializers import AddressSerializer


@address_schema
class AddressViewSet(viewsets.ModelViewSet):
    """
    Adresy zalogowanego klienta; cudze adresy są niewidoczne (404).

    Actions:
    - list:           GET    /customers/addresses/
    - retrieve:       GET    /customers/addresses/{id}/
    - create:         POST   /customers/addresses/
    - update:         PUT    /customers/addresses/{id}/
    - partial_update: PATCH  /customers/addresses/{id}/
    - destroy:        DELETE /customers/addresses/{id}/
    - set_default:    PATCH  /customers/addresses/{id}/set-default/
    """

    permission_classes = [IsAuthenticated]
    serializer_class = AddressSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Address.objects.none()
        return Address.objects.filter(profile__user=self.request.user)

    def perform_create(self, serializer):
        profile = getattr(self.request.user, "profile", None)

        if profile is None:
            raise ValidationError("User profile does not exist")

        serializer.save(profile=profile)

    @action(detail=True, methods=["patch"], url_path="set-default")
    def set_default(self, request, pk=None):
        address = self.get_object()

        if address.is_default:
            return Response(
                self.get_serializer(address).data,
                status=status.HTTP_200_OK,
            )

        # Zdjęcie flagi z pozostałych i ustawienie jej tu to jedna zmiana —
        # bez transakcji błąd zapisu zostawiłby profil bez adresu domyślnego.
        # Blokada profilu kolejkuje równoległe wywołania dla tego samego konta.
        with transaction.atomic():
            Profile.objects.select_for_update().get(pk=address.profile_id)  # type: ignore[missing-attribute]
            Address.objects.filter(profile__user=request.user).exclude(
                pk=address.pk,
            ).update(is_default=False)
            address.is_default = True
            address.save()
        return Response(self.get_serializer(address).data, status=status.HTTP_200_OK)
