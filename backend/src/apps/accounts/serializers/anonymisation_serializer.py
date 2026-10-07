from rest_framework import serializers


class AccountAnonymisationSerializer(serializers.Serializer):
    """Potwierdzenie anonimizacji: hasło konta albo kod z maila (konto bez hasła)."""

    password = serializers.CharField(
        required=False, write_only=True, trim_whitespace=False
    )
    code = serializers.CharField(required=False, write_only=True, max_length=6)


class AccountAnonymisationDetailSerializer(serializers.Serializer):
    detail = serializers.CharField()
