# Linki z maili na jedną domenę webu, uwierzytelnianie kodem

Backend składa wszystkie linki w mailach z jednej zmiennej `FRONTEND_URL`. Na środowisku deweloperskim to `http://localhost:3000`, a adres wpisany na sztywno znika. W produkcji web ma jedną kanoniczną domenę: na nią prowadzą wszystkie linki z maili i pod nią leżą pliki `/.well-known/*` (AASA i `assetlinks.json`, serwowane przez Next). Przed `/.well-known/*` nie może być żadnego przekierowania. Domenę, hosting i ewentualny osobny host API wybieramy przy wdrożeniu. Każdy link ma prefiks języka z `PreferredLanguage`. Aplikacja przejmuje oba prefiksy, ale ignoruje język z URL, bo ma własny ([ADR 0035](0035-next-intl-z-prefiksem-jezyka-waluta-z-kraju-dostawy.md)).

Reset hasła odbywa się kodem, tak jak weryfikacja e-maila. W uwierzytelnianiu nie ma więc żadnego linku z tokenem.

Potwierdzenie zapisu do newslettera i wypis to strony z przyciskiem, a akcja zachodzi dopiero po POST, bo skanery poczty otwierają linki samoczynnie. Maile marketingowe niosą nagłówki `List-Unsubscribe` i `List-Unsubscribe-Post` (RFC 8058).

Aplikacja przejmuje strony produktów, konta i zamówień klienta z kontem. Newsletter, strony prawne, treści sklepu, kasa gościa i strona zamówienia gościa zostają w przeglądarce. W mailach transakcyjnych śledzenie kliknięć u dostawcy maili jest wyłączone. Android używa Play App Signing, a `assetlinks.json` zawiera odciski obu kluczy. Trasa AASA i `associatedDomains` powstają od razu, z Team ID ze zmiennej, a test na urządzeniu czeka na wydanie iOS.

Klient z kontem dostaje w mailu o zamówieniu link do strony zamówienia, która wymaga zalogowania. Gość w każdym mailu po opłaceniu dostaje link „Zobacz zamówienie” z `OrderAccessToken`. Link prowadzi na web i daje wyłącznie odczyt: status, pozycje, numer przesyłki i dokument sprzedaży.

## Considered Options

- **Reset hasła linkiem.** Odrzucone, bo zostawia token w URL, w historii przeglądarki i w zasięgu skanerów, a do tego wymaga deep linku.
- **Akcja newslettera przy samym otwarciu linku.** Odrzucone, bo skanery poczty potwierdzałyby zapisy bez udziału człowieka.
- **Gość bez dostępu do zamówienia, wyłącznie treść maila.** Odrzucone, bo gość musi móc pobrać dokument sprzedaży i śledzić przesyłkę.
- **Strona pośrednia wykrywająca aplikację albo deferred deep linking.** Odrzucone, bo systemowy fallback do przeglądarki pokrywa przypadek braku aplikacji.

## Consequences

Backend dostaje:
- `FRONTEND_URL`,
- włączony reset hasła kodem,
- token dostępu gościa na zamówieniu i endpoint odczytu zamówienia po tokenie,
- nagłówki RFC 8058.

Web dostaje:
- trasy `/.well-known/*`,
- strony newslettera,
- stronę zamówienia gościa.

Anulowanie i zwrot przez gościa, formularz „Sprawdź zamówienie” oraz ważność tokenu po założeniu konta rozstrzyga plasterek zamówień.
