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
    ReturnRequest,
    SalesDocument,
    SalesDocumentKind,
)
from common.money import Money
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


def issue_correction(request: ReturnRequest) -> SalesDocument | None:
    """Korekta rozliczonego zwrotu — jedna na zgłoszenie (ADR 0014, 0026)."""
    if request.settled_at is None:
        return None
    return issue_document(
        request.order, SalesDocumentKind.CORRECTION, return_request=request
    )


@transaction.atomic
def issue_document(
    order: Order, kind: str, *, return_request: ReturnRequest | None = None
) -> SalesDocument:
    """Jeden dokument danego rodzaju: istniejący albo nowo wystawiony.

    Blokada wiersza zamówienia szereguje równoległe uruchomienia zadania dla
    tego samego zamówienia — drugie zastaje dokument pierwszego. Numer,
    PDF i wiersz idą w jednej transakcji: nieudany render cofa też numer,
    więc w numeracji nie zostaje luka.
    """
    order = Order.objects.select_for_update().get(pk=order.pk)
    existing = SalesDocument.objects.filter(
        order=order, kind=kind, return_request=return_request
    ).first()
    if existing is not None:
        return existing

    issued_on = timezone.localdate(timezone=SHOP_TIME_ZONE)
    document = SalesDocument(
        order=order,
        kind=kind,
        number=next_number(kind, issued_on.year),
        year=issued_on.year,
        issued_on=issued_on,
        return_request=return_request,
    )
    # ponytail: plik zapisany przed commitem zostaje osierocony, gdy commit
    # padnie — sprzątanie bucketa dołożyć, jeśli to się kiedyś zdarzy.
    document.object_key = DocumentStorage().save(
        f"sales-documents/{document.year}/{kind}-{document.number}.pdf",
        ContentFile(render_pdf(document)),
    )
    document.save()
    _notify_document_ready(order, document)
    return document


def _notify_document_ready(order: Order, document: SalesDocument) -> None:
    """Powiadamia o nowo wystawionym dokumencie (#156, transakcyjne).

    `robust=True`: awaria powiadomienia nie może cofnąć albo zablokować
    innych callbacków tej transakcji — dokument jest już wystawiony.
    E-mail idzie na `order.email` (kopia z chwili złożenia), nie na
    `user.email`, który mógł się od tamtej pory zmienić.
    """
    from apps.notifications.models import NotificationKind
    from apps.notifications.services import notify

    recipient = order.user if order.user_id is not None else order.email  # type: ignore[missing-attribute]
    payload = {
        "order_number": order.number,
        "document_kind": document.get_kind_display(),  # type: ignore[missing-attribute]
    }
    transaction.on_commit(
        lambda: notify(
            recipient,  # type: ignore[bad-argument-type]
            NotificationKind.DOCUMENT_READY,
            payload,
            email=order.email,
        ),
        robust=True,
    )


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
            **_correction_context(document),
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


def _correction_context(document: SalesDocument) -> dict:
    """Dane korekty: dokument korygowany, przyczyna, pozycje i rozliczenie."""
    request = document.return_request
    if request is None:
        return {}
    from apps.orders.services.settlement import (
        compensation_form,
        item_value,
        refunded_items,
    )

    corrected = (
        SalesDocument.objects.filter(
            order=document.order,
            kind__in=(SalesDocumentKind.INVOICE, SalesDocumentKind.CONFIRMATION),
        )
        .order_by("-kind")
        .first()
    )
    lines = [
        {"item": line, "value": Money(item_value(line), request.currency)}
        for line in refunded_items(request)
    ]
    return {
        "return_request": request,
        "corrected_document": corrected,
        "returned_lines": lines,
        "shipping_refund": request.compensation_money
        - sum((line["value"] for line in lines), start=Money.zero(request.currency)),
        "compensation_form": compensation_form(request),
    }
