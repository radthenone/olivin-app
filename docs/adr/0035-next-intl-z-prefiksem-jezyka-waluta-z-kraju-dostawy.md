# next-intl z prefiksem języka, waluta z kraju dostawy

Interfejs tłumaczymy biblioteką `next-intl` na webie i jej rdzeniem `use-intl` na mobile. Wspólny katalog komunikatów w formacie ICU mieszka w pakiecie `@olivin/i18n`: plik `pl.json` jest źródłem, `en.json` tłumaczeniem, a przestrzenie nazw odpowiadają obszarom funkcji. Klucze są typowane na podstawie `pl.json`. `@olivin/money` pozostaje niezależne od biblioteki i przyjmuje locale jako argument. Na Hermesie dokładamy polyfille `@formatjs/intl-pluralrules` i `intl-locale` z danymi tylko dla `pl` i `en`, bo bez nich psują się polskie formy liczby mnogiej. Warunek: test na urządzeniu potwierdzi, że RN nie ma `Intl.PluralRules`.

Każda strona dla klienta ma prefiks `/pl/` albo `/en/`. Bez prefiksu zostają tylko adresy techniczne: `/api/*`, `/.well-known/*`, `robots.txt`, `sitemap.xml` i pliki statyczne. Wejście na `/` przekierowuje według cookie języka, potem `Accept-Language`, a domyślnie na `/pl`. Ścieżek nie tłumaczymy, bo slug jest jeden i angielski. Na mobile domyślny jest język systemu z możliwością nadpisania w ustawieniach. Klient API wysyła `Accept-Language` z tego samego źródła co interfejs, żeby treści katalogu zgadzały się z resztą ekranu.

Maile wybierają język według preferowanego języka klienta (`PreferredLanguage`), a nie według kraju. Źródło tej wartości:
- konto: nowe pole w profilu,
- gość: wartość zapisana na zamówieniu,
- subskrypcja newslettera: wartość z chwili zapisu.

Gdy wartości brak, maile idą po polsku.

Język i waluta są niezależne. O walucie decyduje kraj dostawy (`DeliveryCountry`): Polska oznacza złote, inny kraj Unii euro. Przed kasą klient ustawia kraj przełącznikiem „Wysyłka do” w nagłówku. Wybór trafia do cookie, a u zalogowanego także do profilu. W kasie rozstrzyga adres dostawy. Jego zmiana przelicza koszyk, a klient dostaje komunikat o przeliczeniu waluty. Kraje spoza Unii nie występują w ogóle. Geolokalizacja służy wyłącznie do banera z sugestią, który nigdy niczego nie przełącza sam, zgodnie z rozporządzeniem o geoblokowaniu. Baner działa tylko wtedy, gdy żądanie ma nagłówek `CF-IPCountry`, i jest renderowany poza keszem ([ADR 0034](0034-katalog-keszowany-z-rewalidacja-na-zdarzenie-cena-jako-dziura-dynamiczna.md)).

## Considered Options

- **i18next.** Dojrzała biblioteka, ale na RN waży dwa do trzech razy więcej, polskie formy liczby mnogiej w ICU wymagają wtyczki, a typowane argumenty działają tylko przy katalogach w `.ts`.
- **Lingui.** Najmniejszy runtime, ale makra wymagają transformacji kodu współdzielonego w obu bundlerach i dodatkowego kroku kompilacji katalogów, wbrew [ADR 0005](0005-pakiety-wspoldzielone-jako-zrodlo.md).
- **Polski bez prefiksu.** Odrzucone na rzecz jednolitych adresów dla obu języków.
- **Waluta wybierana niezależnie od kraju.** Odrzucone, bo [ADR 0019](0019-sprzedaz-do-ue-w-euro-po-polskim-vat.md) wiąże euro z dostawą do Unii.
- **Baza GeoLite2.** Odrzucone, bo wymaga konta, licencji i regularnej aktualizacji bazy dla funkcji, która jest tylko sugestią.

## Consequences

Tłumaczenia trzymamy w JSON w repo, bez zewnętrznego narzędzia. Zadanie `i18n:fill` uzupełnia w `en.json` klucze obecne w `pl.json`, a brakujące w `en.json`, tłumacząc je przez kontener LibreTranslate. Nigdy nie nadpisuje istniejących kluczy, chroni placeholdery ICU i pomija komunikaty z `plural` i `select`. Wynik przegląda człowiek w PR. Backend dostaje pole preferowanego języka w profilu i na zamówieniu, a także kraj dostawy w profilu.
