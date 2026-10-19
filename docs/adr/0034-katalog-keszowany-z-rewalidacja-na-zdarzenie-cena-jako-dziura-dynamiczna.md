# Katalog keszowany z rewalidacją na zdarzenie, cena jako dziura dynamiczna

Strony listy i produktu na webie są statyczne i keszowane (Cache Components w Next.js: `"use cache"` z `cacheTag`). Backend po dwóch zdarzeniach woła endpoint rewalidacji w Next z sekretem i listą tagów: po zapisie lub publikacji produktu oraz po zakończeniu przeliczenia cen. Przeliczenie następuje po aktywacji kursu kruszcu albo odświeżeniu kursu euro. Każda strona i tak wygasa po kilku minutach jako siatka bezpieczeństwa.

Stan magazynowy pokazujemy jako kategorię: dostępny, „ostatnie sztuki” albo niedostępny. Odświeża się tylko z wygaśnięciem strony, bo ostateczną prawdą o cenie i stanie jest koszyk i rezerwacja.

Waluta nie trafia ani do URL, ani do kesza. Cena jest dynamicznym fragmentem strony, który czyta cookie waluty i jest streamowany w tym samym żądaniu. Bez cookie, czyli także dla botów, cena jest w złotych. O walucie decyduje kraj dostawy wybrany jawnie przez klienta. Wybór zapisuje się w cookie, a u zalogowanego także w profilu ([ADR 0035](0035-next-intl-z-prefiksem-jezyka-waluta-z-kraju-dostawy.md)). Nie zgadujemy waluty z geolokalizacji IP ani z języka.

Komponenty serwerowe pobierają dane katalogu przez osobny, publiczny transport serwerowy, bez cookies sesji. Interaktywne wyspy dostają dane przez hydratację pod kluczami Orvala ([ADR 0033](0033-hooki-orvala-wprost-logika-domeny-w-pakiecie-features.md)).

## Considered Options

- **Wyłącznie wygasanie czasowe.** Odrzucone. Po aktywacji kursu strona przez kilka minut pokazywałaby inną cenę niż kasa, a cena na stronie ma znaczenie prawne.
- **Pełne renderowanie przy każdym żądaniu.** Odrzucone. Każde wejście, także bota, obciąża Django, a ceny zmieniają się skokowo, nie w sposób ciągły.
- **Rewalidacja przy każdym ruchu magazynowym.** Odrzucone. Generuje dużo ruchu dla rzadkiego przypadku, który koszyk i tak wyłapie.
- **Waluta w adresie strony.** Odrzucone, bo powstają duplikaty treści dla wyszukiwarek.

## Consequences

Backend dostaje jednego klienta rewalidacji wywoływanego po zatwierdzeniu transakcji. Jeśli web jest niedostępny, zmiana pojawi się po wygaśnięciu strony. Żaden komponent serwerowy katalogu nie może korzystać z sesji użytkownika, bo jego wynik trafia do wspólnego kesza.

## Kontrakt rewalidacji (#318)

- Żądanie: `POST {FRONTEND_URL}/api/revalidate`, nagłówek `X-Revalidate-Secret: <REVALIDATE_SECRET>`, treść `{"tags": [...]}`.
- Tagi: `product:<slug>` przy każdym zapisie produktu z adresem; `catalog` przy publikacji, zdjęciu produktu ze sklepu i po przeliczeniu cen.
- Web musi wyłączyć `/api` z matchera middleware next-intl. Inaczej przekierowanie 301 na prefiks języka zamieni POST na GET (`requests` tak robi) i rewalidacja przepadnie po cichu.
