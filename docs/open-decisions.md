# Otwarte decyzje i praca odłożona

Rejestr rozstrzygnięć, które muszą zapaść, zanim powstaną odpowiadające im
fragmenty systemu, oraz pracy świadomie odłożonej. Każda pozycja mówi, czego
dotyczy, co blokuje, kto rozstrzyga i jakie są opcje.

Gdy decyzja zapada, jej uzasadnienie trafia do `docs/adr/`, a pozycja znika
stąd. Gdy praca odłożona rusza, wraca na tracker jako zadanie z zakresem.

## Stan modelu w chwili pisania

Aplikacje `products` i `orders` są pustymi szkieletami po `startapp`. Decyzje
zapisane w ADR-ach opisują model, który dopiero powstanie — żaden z nich nie
jest jeszcze zaimplementowany.

---

## Praca odłożona

### Podniesienie Expo z SDK 54 do SDK 57

Zablokowane upstream. Dev Client nie potrafi pobrać bundla z Metro — parser
chunked encoding po stronie React Native desynchronizuje się, chociaż ten sam
strumień pobrany z hosta jest poprawny. Bez działającego bundla nie da się
sprawdzić logowania, stylowania ani tokenów.

Właściciel rozstrzygnie termin powrotu do tematu samodzielnie.

Żywym artefaktem tej pracy pozostaje **draft PR #59** wraz z pełną diagnostyką.

Zmiana z tej gałęzi niezależna od SDK została już wydzielona i zmergowana:
wykluczenie katalogów wynikowych z obserwatora plików Metro (PR #88).

W gałęzi zostają jeszcze dwie zmiany, świadomie nieprzenoszone:

- usunięcie `@rnrepo/expo-config-plugin` — to realna zależność wpięta
  w `app.config.js`; usunięcie zmienia konfigurację builda natywnego,
  a weryfikacja wymaga `expo prebuild` i Android SDK
- `StatusBar` bez `backgroundColor` — na SDK 54 atrybut nadal działa, więc
  usunięcie go byłoby zmianą wyglądu bez powodu

Przy wznawianiu: odnośnik do zgłoszenia upstream podany w opisie #59 nie zgadza
się z opisem blokady i wymaga poprawienia.

---

## Pomysły na przyszłość

Oznaczone na trackerze etykietą `future-idea`. Nie są zaplanowaną pracą — są
zapisem kierunku, żeby nie trzeba było odtwarzać rozumowania od zera.

### Sprzedaż firmom wraz z fakturowaniem i KSeF

Sklep prowadzi wyłącznie sprzedaż konsumencką — patrz
[ADR 0016](adr/0016-sprzedaz-wylacznie-konsumencka.md). Wejście w sprzedaż
firmom oznacza dołożenie fakturowania, integracji z Krajowym Systemem e-Faktur
oraz innych zasad zwrotów, ponieważ ochrona konsumencka nie obejmuje transakcji
między przedsiębiorcami.

Przed podjęciem tematu stan przepisów i obowiązujące terminy wymagają
potwierdzenia u księgowości — zmieniały się wielokrotnie.

### Terraform jako warstwa infrastruktury jako kodu

Dziś jedynym opisem wdrożenia jest `docker-compose.prod.yml`, nakładany na host
ręcznie. Nic nie opisuje hosta, bazy, magazynu obiektów, sieci ani sekretów.

Praca nie może ruszyć przed wyborem platformy — Terraform bez wybranego dostawcy
to pisanie w próżnię.

| Opcja | Dokąd prowadzi |
| --- | --- |
| VPS z obecnym compose | Najtaniej i najszybciej, Terraform opisuje serwer, DNS i kopie zapasowe |
| Kontenery zarządzane | Skalowanie i mniej utrzymania, w zamian przepisanie opisu wdrożenia |
| PaaS | Najmniej infrastruktury i najmniej kontroli, najdroższe przy wzroście |

Rekomendacja: VPS wraz z tym, co już istnieje. Na etapie przed pierwszą
sprzedażą skalowanie nie jest problemem, którego warto szukać.

Sprawa wymagająca uwagi niezależnie od wyboru: repozytorium jest publiczne.
Sekrety muszą trafiać do usług przez zmienne środowiskowe na hoście albo
menedżer sekretów — nigdy do stanu Terraforma, który potrafi przechowywać
wartości jawnie.

---

## Rozstrzygnięte

Decyzje właściciela z 16 września 2026 przeniesione do ADR-ów:

| Zagadnienie | Rozstrzygnięcie | ADR |
| --- | --- | --- |
| Złoto inwestycyjne i stawka podatku | Sprzedajemy; stawka przy wariancie, zwolnienie osobną flagą | [0013](adr/0013-stawka-vat-przy-wariancie.md) |
| Podatek od kuponów ze zwrotu | Zwrot jest korektą, kupon formą zapłaty; tylko dla klientów indywidualnych | [0014](adr/0014-zwrot-jako-korekta-kupon-jako-zaplata.md) |
| Forma rekompensaty przy zwrocie | Rozstrzyga podstawa zwrotu zapisana w `ReturnReason` | [0015](adr/0015-podstawa-zwrotu-decyduje-o-formie-rekompensaty.md) |
| Fakturowanie i KSeF | Wyłącznie sprzedaż konsumencka, bez KSeF | [0016](adr/0016-sprzedaz-wylacznie-konsumencka.md) |
| Sposób ustalania cen | Ręcznie, ze wstępnym wyliczeniem od próby i kursu kruszcu | [0017](adr/0017-cena-reczna-ze-wstepnym-wyliczeniem.md) |
| Personalizacja produktów | Grawer opcjonalny, osobna pozycja ceny, wyłącza prawo odstąpienia | [0018](adr/0018-grawer-jako-opcja-wylaczajaca-zwrot.md) |
| Sprzedaż transgraniczna | Polska i Unia, ceny w euro, polski podatek, model gotowy na stawkę per kraj | [0019](adr/0019-sprzedaz-do-ue-w-euro-po-polskim-vat.md) |
| Testy końcowe aplikacji mobilnej | Maestro | [0020](adr/0020-maestro-do-testow-mobilnych.md) |
| Back office | Django admin, dopuszczalna nakładka wyglądowa | [0021](adr/0021-django-admin-jako-back-office.md) |
| GitHub jako logowanie | Skreślony | — |

Dwie pozycje wymagają potwierdzenia u księgowości, mimo że decyzja zapadła:
kwalifikacja złota inwestycyjnego ([0013](adr/0013-stawka-vat-przy-wariancie.md))
oraz zastosowanie polskiej stawki do sprzedaży konsumenckiej w Unii wraz ze
stanem obrotu wobec progu sprzedaży wysyłkowej
([0019](adr/0019-sprzedaz-do-ue-w-euro-po-polskim-vat.md)).

Regulamin zwrotów i kuponów wymaga przeglądu przez prawnika przed uruchomieniem
sprzedaży ([0015](adr/0015-podstawa-zwrotu-decyduje-o-formie-rekompensaty.md)).
