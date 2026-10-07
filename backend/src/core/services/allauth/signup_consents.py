"""Zgody przy zakładaniu konta (#207, `CONTEXT.md` Consent).

Moduł nie importuje `allauth.account.forms`: allauth dziedziczy po
`SignupConsentsForm` (`ACCOUNT_SIGNUP_FORM_CLASS`) przy imporcie własnych
formularzy, więc import w drugą stronę byłby cykliczny.
"""

from __future__ import annotations

import logging

from django import forms
from django.contrib.auth.base_user import AbstractBaseUser
from django.http import HttpRequest

from apps.consents.models import Consent, ConsentDocument, ConsentKind
from apps.notifications.models import NotificationPreference

logger = logging.getLogger(__name__)

CONSENT_FIELDS: dict[str, str] = {
    ConsentKind.TERMS: "consent_terms",
    ConsentKind.PRIVACY: "consent_privacy",
    ConsentKind.MARKETING: "consent_marketing",
}
SIGNUP_DOCUMENTS_KEY = "consent_documents"


class SignupConsentsForm(forms.Form):
    """Pola zgód wspólne dla rejestracji e-mailem i provider signup.

    `clean()` ustala bieżące wersje dokumentów, na które klient się zgodził,
    i odkłada je w `cleaned_data` — zapisuje je adapter konta w transakcji
    zakładającej użytkownika (`record_signup_consents`).
    """

    consent_terms = forms.BooleanField(
        required=True,
        error_messages={"required": "Akceptacja regulaminu jest wymagana."},
        help_text="Zgoda na bieżącą wersję regulaminu (wymagana)",
    )
    consent_privacy = forms.BooleanField(
        required=True,
        error_messages={"required": "Akceptacja polityki prywatności jest wymagana."},
        help_text="Zgoda na bieżącą wersję polityki prywatności (wymagana)",
    )
    consent_marketing = forms.BooleanField(
        required=False,
        initial=False,
        help_text="Zgoda na komunikację marketingową e-mailem (opcjonalna)",
    )

    def clean(self) -> dict:
        cleaned_data = super().clean() or {}
        documents = []
        for kind, field in CONSENT_FIELDS.items():
            if not cleaned_data.get(field):
                continue
            document = ConsentDocument.objects.current(kind)
            if document is None:
                logger.error("Brak obowiązującej wersji dokumentu zgody: %s", kind)
                raise forms.ValidationError(
                    "Rejestracja jest chwilowo niemożliwa: brak obowiązującej "
                    f"wersji dokumentu „{ConsentKind(kind).label}” (błąd "
                    "konfiguracji sklepu).",
                    code="consent_document_missing",
                )
            documents.append(document)
        cleaned_data[SIGNUP_DOCUMENTS_KEY] = documents
        return cleaned_data

    def signup(self, request: HttpRequest, user: AbstractBaseUser) -> None:
        """Wymagane przez allauth; zgody zapisuje już `record_signup_consents`."""


def record_signup_consents(user: AbstractBaseUser, cleaned_data: dict) -> None:
    """Zapisuje zgody z rejestracji i ustawia zgodę marketingową e-mail.

    Wywoływane z `save_user` adaptera konta — w tej samej transakcji co
    konto i profil, także przy provider signup.
    """
    documents: list[ConsentDocument] = cleaned_data.get(SIGNUP_DOCUMENTS_KEY, [])
    for document in documents:
        Consent.objects.create(user=user, document=document)
    if any(d.kind == ConsentKind.MARKETING for d in documents):
        NotificationPreference.objects.update_or_create(
            user=user, defaults={"marketing_email": True}
        )
