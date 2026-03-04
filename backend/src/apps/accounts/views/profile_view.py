from rest_framework import status, viewsets
from rest_framework.decorators import action, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import Profile, RoleChoices
from apps.accounts.schema import change_role_schema
from apps.accounts.serializers import ProfileSerializer


class ProfileViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing profile instances.

    Actions:
    - list:           GET  /api/v1/profiles/
    - retrieve:       GET  /api/v1/profiles/{id}/
    - create:         POST /api/v1/profiles/
    - update:         PUT  /api/v1/profiles/{id}/
    - partial_update: PATCH /api/v1/profiles/{id}/
    - destroy:        DELETE /api/v1/profiles/{id}/
    - change_role:    PATCH /api/v1/profiles/{id}/change-role/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ProfileSerializer

    def get_queryset(self):
        return Profile.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @change_role_schema
    @action(detail=True, methods=['patch'], url_path='change-role', permission_classes=[IsAuthenticated])
    def change_role(self, request, pk=None):
        profile = self.get_object()
        if profile.role == RoleChoices.CUSTOMER:
            profile.role = RoleChoices.ADMIN
        else:
            profile.role = RoleChoices.CUSTOMER
        profile.save()
        return Response(self.get_serializer(profile).data, status=status.HTTP_200_OK)
