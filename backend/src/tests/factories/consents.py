from __future__ import annotations

import datetime

from factory.declarations import Sequence, SubFactory
from factory.django import DjangoModelFactory

from apps.consents.models import Consent, ConsentDocument, ConsentKind
from tests.factories.accounts import UserFactory


class ConsentDocumentFactory(DjangoModelFactory):
    """Regulamin obowiązujący od dawna — bieżąca wersja, o ile nie ma nowszej."""

    class Meta:
        model = ConsentDocument

    kind = ConsentKind.TERMS
    version = Sequence(lambda n: f"v{n + 1}")
    effective_from = datetime.date(2026, 1, 1)


class ConsentFactory(DjangoModelFactory):
    """Zgoda zalogowanego klienta na dokument z fabryki."""

    class Meta:
        model = Consent

    user = SubFactory(UserFactory)
    document = SubFactory(ConsentDocumentFactory)


class GuestConsentFactory(ConsentFactory):
    """Zgoda gościa — po e-mailu, bez konta."""

    user = None
    email = Sequence(lambda n: f"guest{n}@test.com")
