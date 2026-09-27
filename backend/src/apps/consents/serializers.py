from __future__ import annotations

from rest_framework import serializers

from apps.consents.models import Consent, ConsentDocument


class ConsentDocumentSerializer(serializers.ModelSerializer):
    """Bieżąca wersja dokumentu — tyle, ile klient potrzebuje, żeby ją
    pokazać i odesłać w zgodzie."""

    class Meta:
        model = ConsentDocument
        fields = ["id", "kind", "version", "effective_from"]
        read_only_fields = fields


class ConsentSerializer(serializers.ModelSerializer):
    """Zapis zgody: dokument z listy bieżących wersji plus podmiot.

    Podmiot bierze się z żądania — zalogowany klient z uwierzytelnienia,
    gość z pola `email`. Klient nie wskazuje użytkownika jawnie, więc nie
    da się zapisać zgody w cudzym imieniu.
    """

    email = serializers.EmailField(
        required=False,
        write_only=True,
        help_text="E-mail gościa; pomijany przy zalogowanym kliencie",
    )
    kind = serializers.CharField(source="document.kind", read_only=True)

    class Meta:
        model = Consent
        fields = ["id", "document", "email", "kind", "version", "granted_at"]
        read_only_fields = ["id", "kind", "version", "granted_at"]

    def validate_document(self, document: ConsentDocument) -> ConsentDocument:
        if ConsentDocument.objects.current(document.kind) != document:
            raise serializers.ValidationError(
                "To nie jest bieżąca wersja dokumentu — pobierz listę ponownie."
            )
        return document

    def validate(self, attrs: dict) -> dict:
        user = self.context["request"].user
        email = attrs.get("email", "")
        if user.is_authenticated:
            if email:
                raise serializers.ValidationError(
                    {
                        "email": "Zalogowany klient udziela zgody na konto, nie na e-mail."
                    }
                )
            attrs["user"] = user
        elif not email:
            raise serializers.ValidationError(
                {"email": "Gość podaje e-mail, na który zapisujemy zgodę."}
            )
        return attrs
