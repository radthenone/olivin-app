"""Dokumenty sprzedaży: numeracja, render PDF i zapis w buckecie (ADR 0026)."""

from __future__ import annotations

from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from django.template.loader import render_to_string
from django.utils import timezone

from apps.orders.models import (
    DocumentCounter,
    Order,
    OrderStatus,
    SalesDocument,
    SalesDocumentKind,
)
from core.storage.storages import DocumentStorage

# Data i rok dokumentu liczą się w czasie sklepu, nie serwera (UTC): wpłata
# tuż po północy w sylwestra należy już do nowego roku numeracji.
SHOP_TIME_ZONE = ZoneInfo("Europe/Warsaw")


def kinds_for(order: Order) -> list[str]:
    """Rodzaje wystawiane po zapłacie: potwierdzenie zawsze, faktura na prośbę."""
    kinds: list[str] = [SalesDocumentKind.CONFIRMATION]
    if order.invoice_requested:
        kinds.append(SalesDocumentKind.INVOICE)
    return kinds


def issue_documents(order: Order) -> list[SalesDocument]:
    """Wystawia dokumenty opłaconego zamówienia; powtórka niczego nie dubluje.

    Zamówienie nieopłacone nie dostaje nic — dokument potwierdza sprzedaż,
    której jeszcze nie było.
    """
    if order.status == OrderStatus.PENDING:
        return []
    return [issue_document(order, kind) for kind in kinds_for(order)]


@transaction.atomic
def issue_document(order: Order, kind: str) -> SalesDocument:
    """Jeden dokument danego rodzaju: istniejący albo nowo wystawiony.

    Blokada wiersza zamówienia szereguje równoległe uruchomienia zadania dla
    tego samego zamówienia — drugie zastaje dokument pierwszego. Numer,
    PDF i wiersz idą w jednej transakcji: nieudany render cofa też numer,
    więc w numeracji nie zostaje luka.
    """
    order = Order.objects.select_for_update().get(pk=order.pk)
    existing = SalesDocument.objects.filter(order=order, kind=kind).first()
    if existing is not None:
        return existing

    issued_on = timezone.localdate(timezone=SHOP_TIME_ZONE)
    document = SalesDocument(
        order=order,
        kind=kind,
        number=next_number(kind, issued_on.year),
        year=issued_on.year,
        issued_on=issued_on,
    )
    # ponytail: plik zapisany przed commitem zostaje osierocony, gdy commit
    # padnie — sprzątanie bucketa dołożyć, jeśli to się kiedyś zdarzy.
    document.object_key = DocumentStorage().save(
        f"sales-documents/{document.year}/{kind}-{document.number}.pdf",
        ContentFile(render_pdf(document)),
    )
    document.save()
    return document


@transaction.atomic
def next_number(kind: str, year: int) -> int:
    """Kolejny numer w obrębie rodzaju i roku, nadany atomowo.

    Wiersz licznika jest blokowany do końca transakcji wołającego, więc
    równoległe wywołanie czeka i dostaje numer następny — bez luki i bez
    duplikatu. Pierwszy numer roku zakłada wiersz; wyścig o jego założenie
    rozstrzyga ograniczenie unikalności, a `get_or_create` ponawia odczyt.
    """
    # ponytail: blokada trwa do końca transakcji wołającego, także przez
    # render PDF — wystawianie jest szeregowane w obrębie rodzaju i roku.
    # Przy dziesiątkach dokumentów na minutę renderować przed nadaniem numeru.
    counter, _ = DocumentCounter.objects.select_for_update().get_or_create(
        kind=kind, year=year
    )
    counter.last_number += 1
    counter.save(update_fields=["last_number"])
    return counter.last_number


def render_pdf(document: SalesDocument) -> bytes:
    """PDF z szablonu Django przez WeasyPrint wywoływany wprost (ADR 0026)."""
    # Import leniwy: WeasyPrint ładuje Pango przy imporcie, a biblioteki
    # systemowe są potrzebne tylko tam, gdzie dokument faktycznie powstaje.
    from weasyprint import HTML

    order = document.order
    html = render_to_string(
        "orders/sales_document.html",
        {
            "document": document,
            "order": order,
            "items": order.items.all(),  # type: ignore[missing-attribute]
            "seller": {
                "name": settings.SELLER_NAME,
                "address": settings.SELLER_ADDRESS,
                "tax_id": settings.SELLER_TAX_ID,
            },
        },
    )
    # Bez celu zapisu WeasyPrint zawsze zwraca bajty; `None` jest tylko
    # w sygnaturze, dla wariantu z plikiem docelowym.
    pdf = HTML(string=html).write_pdf()
    assert pdf is not None
    return pdf
