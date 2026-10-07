from django.contrib.auth import logout
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.schema import (
    account_anonymise_code_schema,
    account_anonymise_schema,
)
from apps.accounts.serializers import AccountAnonymisationSerializer
from apps.accounts.services import anonymisation_code
from apps.accounts.services.anonymisation_service import (
    ActiveOrderError,
    StaffAccountError,
    anonymise_account,
    has_active_order,
)

_ACTIVE_ORDER = {
    "detail": "Nie można usunąć konta, dopóki trwa niedostarczone zamówienie."
}
_STAFF = {"detail": "Konto obsługi sklepu — skontaktuj się z administratorem."}


class _AnonymisationView(APIView):
    """Zakres `auth`: potwierdzenie hasłem/kodem nie może być zgadywane seriami."""

    permission_classes = [IsAuthenticated]
    throttle_scope = "auth"


class AccountAnonymiseView(_AnonymisationView):
    """`POST /customers/account/anonymise/` — anonimizacja konta (ADR 0029)."""

    @account_anonymise_schema
    def post(self, request: Request) -> Response:
        payload = AccountAnonymisationSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        user = request.user
        if user.is_staff or user.is_superuser:
            return Response(_STAFF, status=status.HTTP_400_BAD_REQUEST)
        # Najpierw tania odmowa: kod potwierdzenia nie przepada przy 409.
        if has_active_order(user):
            return Response(_ACTIVE_ORDER, status=status.HTTP_409_CONFLICT)
        if user.has_usable_password():
            password = payload.validated_data.get("password", "")
            if not user.check_password(password):
                raise ValidationError({"password": "Nieprawidłowe hasło."})
        else:
            code = payload.validated_data.get("code", "")
            if not anonymisation_code.verify_code(user, code):
                raise ValidationError({"code": "Nieprawidłowy albo wygasły kod."})
        try:
            anonymise_account(user)
        except ActiveOrderError:
            return Response(_ACTIVE_ORDER, status=status.HTTP_409_CONFLICT)
        except StaffAccountError:
            return Response(_STAFF, status=status.HTTP_400_BAD_REQUEST)
        logout(request._request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AccountAnonymiseCodeView(_AnonymisationView):
    """`POST /customers/account/anonymise/code/` — kod dla konta bez hasła."""

    @account_anonymise_code_schema
    def post(self, request: Request) -> Response:
        if request.user.has_usable_password():
            return Response(
                {"detail": "Konto ma hasło — potwierdź usunięcie hasłem."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        anonymisation_code.send_code(request.user)
        return Response(
            {"detail": "Wysłaliśmy kod potwierdzenia na adres konta."},
            status=status.HTTP_202_ACCEPTED,
        )
