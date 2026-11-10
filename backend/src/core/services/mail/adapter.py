from __future__ import annotations

import json
from typing import Any, cast

from allauth.account.adapter import DefaultAccountAdapter
from allauth.core import context as allauth_context
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.http import RawPostDataException
from django.db import transaction
from django.db.transaction import on_commit

from apps.accounts.models import Profile
from apps.accounts.services import update_profile_from_signup_data
from apps.accounts.usernames import (
    USERNAME_MAX_LENGTH,
    USERNAME_MIN_LENGTH,
    is_reserved_username,
    username_chars_validator,
)
from common.languages import (
    PreferredLanguage,
    language_from_request,
    localized_link,
)
from core.services.allauth.signup_consents import record_signup_consents
from core.services.mail.service import MailService
from core.services.mail.tasks import send_email_payloads_task

# Temat i treść maila „konto już istnieje”; klucz to język (ADR 0035).
# Allauth wysyła tu własny szablon, który nie zna nazwy serwisu ani języka
# odbiorcy, a link resetu składa z backendu (#417).
_ACCOUNT_ALREADY_EXISTS_MESSAGES: dict[str, tuple[str, str]] = {
    "pl": (
        "Konto już istnieje — {site_name}",
        "Konto z adresem {email} już istnieje w {site_name}.\n\n"
        "Jeśli zapomniałeś hasła, ustaw nowe na stronie:\n{reset_url}\n\n"
        "Jeśli to nie Ty, zignoruj tę wiadomość.",
    ),
    "en": (
        "Account Already Exists — {site_name}",
        "An account with the address {email} already exists in {site_name}.\n\n"
        "If you forgot your password, set a new one here:\n{reset_url}\n\n"
        "If this wasn't you, ignore this message.",
    ),
}


def get_request_payload(request) -> dict:
    """Zwraca dane requestu także dla headless JSON signup."""
    data = getattr(request, "data", None)
    if data:
        return dict(data)

    post_data = getattr(request, "POST", None)
    if post_data:
        if hasattr(post_data, "dict"):
            return post_data.dict()
        return dict(post_data)

    try:
        body = getattr(request, "body", b"")
    except RawPostDataException:
        return {}

    if not body:
        return {}

    try:
        payload = json.loads(body.decode("utf-8"))
    except (TypeError, ValueError, UnicodeDecodeError):
        return {}

    return payload if isinstance(payload, dict) else {}


class AsyncAccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        """Zapisuje użytkownika allauth, profil i zgody z rejestracji.

        Provider signup przechodzi tędy z `SocialAccountAdapter.save_user`,
        więc zgody trafiają do tej samej transakcji co konto i profil.
        """
        with transaction.atomic():
            saved_user = super().save_user(request, user, form, commit)
            if commit:
                profile = update_profile_from_signup_data(
                    saved_user,
                    get_request_payload(request),
                )
                # Pole formularza wygrywa z nagłówkiem żądania (ADR 0035).
                profile.preferred_language = form.cleaned_data.get(
                    "preferred_language"
                ) or language_from_request(request)
                profile.save(update_fields=["preferred_language", "updated_at"])
                record_signup_consents(saved_user, form.cleaned_data)
            return saved_user

    def send_mail(self, template_prefix: str, email: str, context: dict) -> None:
        self._queue_mail(self.render_mail(template_prefix, email, context))

    def send_account_already_exists_mail(self, email: str) -> None:
        """Wysyła mail „konto już istnieje” w języku odbiorcy (#417).

        Jedyna wskazówka dla kogoś z istniejącym kontem, bo UI celowo pokazuje
        „sprawdź e-mail” (`ACCOUNT_PREVENT_ENUMERATION`). Link prowadzi na
        webowy reset hasła kodem (ADR 0038), nie na endpoint backendu.
        """
        language = self._account_already_exists_language(email, allauth_context.request)
        site_name = settings.SELLER_NAME
        subject, body = _ACCOUNT_ALREADY_EXISTS_MESSAGES[language]
        reset_url = localized_link(
            settings.HEADLESS_FRONTEND_URLS["account_reset_password"], language
        )
        self._queue_mail(
            EmailMultiAlternatives(
                subject=subject.format(site_name=site_name),
                body=body.format(site_name=site_name, email=email, reset_url=reset_url),
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email],
            )
        )

    def _account_already_exists_language(self, email: str, request) -> str:
        """Język maila: preferencja konta, potem żądanie, na końcu polski."""
        preferred = (
            Profile.objects.filter(user__email__iexact=email)
            .values_list("preferred_language", flat=True)
            .first()
        )
        if preferred in PreferredLanguage.values:
            return str(preferred)
        if request is not None:
            return language_from_request(request) or PreferredLanguage.PL
        return PreferredLanguage.PL

    def _queue_mail(self, msg: EmailMessage) -> None:
        payload = MailService.serialize(msg)
        task = cast(Any, send_email_payloads_task)
        on_commit(lambda: task.delay([payload]))

    def populate_username(self, request, user) -> None:
        """Nie wyprowadza nazwy z e-maila/imienia (domyślne allauth).

        Pustą nazwę zostawia modelowi: `CustomUser.save()` nadaje unikalne
        `anon<liczba>` z ponowieniem przy kolizji (#195). Dotyczy też kont
        społecznościowych — allauth woła tę metodę z `SocialAccountAdapter.save_user`.
        """

    def clean_username(self, username: str, shallow: bool = False) -> str:
        """Waliduje nazwę wybraną przy rejestracji regułami profilu (#195).

        Te same ograniczenia co `ProfileSerializer`: długość, dozwolone znaki
        i nazwy zastrzeżone. Unikalność sprawdza allauth (bez wielkości liter),
        więc błąd wraca przy polu `username`.
        """
        if not username:
            return username

        if not USERNAME_MIN_LENGTH <= len(username) <= USERNAME_MAX_LENGTH:
            raise ValidationError(
                f"Nazwa użytkownika musi mieć od {USERNAME_MIN_LENGTH} do "
                f"{USERNAME_MAX_LENGTH} znaków.",
                code="invalid_username",
            )
        if is_reserved_username(username):
            raise ValidationError(
                "Ta nazwa użytkownika jest zarezerwowana.",
                code="username_reserved",
            )
        username_chars_validator(username)

        return super().clean_username(username, shallow=shallow)
