# Otwarte decyzje i praca odłożona

Rejestr rozstrzygnięć, które muszą zapaść, zanim powstaną odpowiadające im
fragmenty systemu, oraz pracy świadomie odłożonej. Każda pozycja mówi, czego
dotyczy, co blokuje, kto rozstrzyga i jakie są opcje.

Gdy decyzja zapada, jej uzasadnienie trafia do `docs/adr/`, a pozycja znika
stąd. Gdy praca odłożona rusza, wraca na tracker jako zadanie z zakresem.

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

### Kampanie marketingowe z harmonogramem i segmentami

Ogłoszenie promocji to dziś ręczna akcja w panelu przy promocji, rozsyłana
trzema kanałami do klientów ze zgodą marketingową i potwierdzonych subskrypcji
newslettera. Osobny byt kampanii — harmonogram, segmenty (premium / wszyscy),
statystyki otwarć — wraca, gdy ręczny przycisk przestanie wystarczać.

### Checkout UI web + mobile

Ekrany kasy — koszyk, dane i adres, dostawa, płatność — dla web i aplikacji
mobilnej. Model kasy jest rozstrzygnięty w
[ADR 0030](adr/0030-koszyk-po-stronie-backendu-i-kasa-w-czterech-krokach.md):
koszyk na backendzie, gość z tokenem, cztery kroki, koszt dostawy znany przed
intencją płatniczą. Interfejs czeka, aż backend koszyka i kasy istnieje —
projektowanie ekranów przed kontraktem API oznaczałoby rysowanie ich dwa razy.
Zapisany kierunek: ikonka koszyka z licznikiem pozycji, rozwijana lista, pełny
widok koszyka jako krok pierwszy, arkusz operatora wysuwany od dołu na mobile
i osadzony element na webie
([ADR 0012](adr/0012-payment-intents-z-gotowymi-elementami.md)). Każdy bilet
backendowy serii #144–#157 niesie sekcję „kontrakt API musi umożliwić", żeby
tej drogi nie zamknąć. Tracker: #158.

### Świadomie poza zakresem pierwszej wersji

Zapisane, żeby nie wracały jako „a może by”: waluty poza złotym i euro,
marketplace z wieloma sprzedawcami, program poleceń, raty i odroczone
płatności, konfigurator 3D z wyceną na żywo, czat i wsparcie na żywo,
własne zdarzenia analityczne z aplikacji mobilnej, adapter kursu kruszcu
(do czasu wyboru dostawcy kurs wpisuje się ręcznie). Raty i polecenia mają
sens po pierwszym roku sprzedaży.

Kolejność platform: na produkcję idą web i Android. iOS jest zgodny w kodzie
i uruchamiany na symulatorze, a wydanie następuje dopiero po tym, jak web i
Android się przyjmą (lista „Przed wydaniem iOS” niżej).

### Web i aplikacja mobilna gotowe do produkcji

Cel: web (Next) i aplikacja na Androida gotowe do produkcji na istniejącym
backendzie. iOS jest zgodny w kodzie i uruchamiany na symulatorze (EAS Build z
Windowsa, Appetize albo EAS Simulator), bez wydania. Rzeczy iOS, które nie
wymagają konta Apple, powstają od razu, na przykład `associatedDomains` i
trasa AASA w Next. Za „gotowe” w tym rejestrze uznajemy stan, w którym
decyzje są zapisane w ADR-ach i `CONTEXT.md`, a każdy plasterek ma issue gotowe
pod `/git-start`. Wdrażanie odbywa się osobnym torem.

Zasady obowiązujące we wszystkich plasterkach:

- Liczy się funkcjonalność, wygląd dopracowujemy później. Na webie shadcn/ui, na mobile RNR, style
  wyłącznie z `packages/tokens`.
- Logika (hooki Orvala, query keys, zod, kwoty) mieszka w `packages`. Web i
  mobile to cienkie warstwy interfejsu
  ([ADR 0001](adr/0001-osobne-aplikacje-web-i-mobile.md),
  [ADR 0005](adr/0005-pakiety-wspoldzielone-jako-zrodlo.md)).
- Ekrany składamy z komponentów biblioteki, a nie z jednorazowych stylów, żeby
  tor designu mógł je później podmienić bez ruszania logiki.

Tryb pracy: jedna pozycja na sesję. Gdy trzeba, najpierw research, potem
`/grill-with-docs`. Rozstrzygnięta pozycja przechodzi do ADR-u i znika z tej
listy. Na koniec plasterka zakładamy issue.

**Decyzje przekrojowe** (w nawiasie, czy wymagają researchu):

1. ~~Gdzie żyją wspólne hooki i query keys.~~ Rozstrzygnięte w
   [ADR 0033](adr/0033-hooki-orvala-wprost-logika-domeny-w-pakiecie-features.md).
2. ~~Strategia renderowania katalogu po stronie serwera.~~ Rozstrzygnięte w
   [ADR 0034](adr/0034-katalog-keszowany-z-rewalidacja-na-zdarzenie-cena-jako-dziura-dynamiczna.md).
3. ~~Biblioteka i18n i waluta.~~ Rozstrzygnięte w
   [ADR 0035](adr/0035-next-intl-z-prefiksem-jezyka-waluta-z-kraju-dostawy.md).
4. ~~Widget wyboru paczkomatu.~~ Rozstrzygnięte w
   [ADR 0036](adr/0036-wysylka-wylacznie-kurierem.md): wyłącznie kurier.
5. ~~Push.~~ Rozstrzygnięte w
   [ADR 0037](adr/0037-push-przez-expo-z-minimum-tresci.md).
6. ~~Deep linki z maili.~~ Rozstrzygnięte w
   [ADR 0038](adr/0038-linki-z-maili-na-jedna-domene-webu-auth-kodem.md).
7. ~~Obserwowalność.~~ Rozstrzygnięte w
   [ADR 0039](adr/0039-glitchtip-na-wlasnym-serwerze-z-sdk-sentry.md). Plasterek
   zaczyna się od testu source map.
8. ~~Testowanie iOS z Windowsa.~~ Rozstrzygnięte zakresem celu: symulator,
   bez wydania (`docs/research/ios-bez-maca.md`).
9. ~~Tor designu.~~ Rozstrzygnięte bez ADR-u, bo decyzję łatwo odwrócić. Opis
   jest w sekcji „Tor designu” niżej.

**Plasterki** w kolejności wynikającej z zależności:

| # | Plasterek | Czeka na |
| --- | --- | --- |
| 0 | Fundament: logowanie na webie, shadcn i tokeny, Playwright, #96 | decyzję 1, bez grillingu |
| 1 | Katalog | 1, 2, 3 |
| 1b | Produkty na zamówienie ([ADR 0024](adr/0024-produkt-na-zamowienie-i-para-jako-jedna-pozycja.md)) | 1 |
| — | SEO | 2 |
| 2 | Koszyk i kasa, #158 ([ADR 0030](adr/0030-koszyk-po-stronie-backendu-i-kasa-w-czterech-krokach.md)) | zadania przed plasterkiem 2 |
| 6 | Zgody i strony prawne | 1 |
| — | Treści sklepu | 2 |
| 3 | Zamówienia po zakupie ([ADR 0026](adr/0026-dokument-sprzedazy-generowany-raz-na-backendzie.md)) | 1, 6 |
| 4 | Konto i preferencje | 1 |
| — | Linki z maili | 6 |
| 5 | Powiadomienia | 5, 6 |
| 7 | Zwroty ([ADR 0031](adr/0031-zwrot-najpierw-kuponem-reszta-pieniedzmi.md)) | 1 |
| 8 | Opinie | 1 |
| — | Back office: przejście codziennych operacji w Django admin | — |
| — | Obserwowalność | 7 |

Plasterki, które mają już ADR, grillujemy głównie pod kątem kontraktu interfejsu.

**Tor designu** (research w `docs/research/claude-design.md`):

- Do Claude Design trafia wyłącznie biblioteka webowa (shadcn, `web/src/components/ui/`)
  i to ona jest systemem referencyjnym. Mobile (RNR) nie jest synchronizowane
  osobno. Trzyma te same nazwy komponentów, warianty i tokeny z `packages/tokens`
  ([ADR 0003](adr/0003-shadcn-na-web-rnr-na-mobile.md)).
- Źródłem prawdy jest kod. W Claude Design powstają makiety z naszych komponentów.
  Zmiana wyglądu wraca do kodu jako zmiana tokenu albo komponentu, na webie i w
  odpowiedniku na mobile, a potem idzie kolejny `/design-sync`.
- Układ plików jest płaski, taki jak generuje CLI shadcn. Zmieniamy go, jeśli
  pierwszy sync wymusi foldery. Komponenty złożone z domeny
  (`web/src/components/<obszar>/`) nie są synchronizowane.
- Komponenty `ui/` są czyste: bez danych, nawigacji i i18n, a style biorą
  wyłącznie z tokenów. Reguła jest zapisana w `.ai/project.md` i
  `frontend/web/AGENTS.md`. Egzekwowanie dochodzi w plasterku 0: ESLint
  `no-restricted-imports` dla `web/src/components/ui/**` (zakaz `@olivin/api`,
  `@olivin/features`, `next-intl`, `next/navigation`) oraz grep w CI na hexy i
  dowolne wartości Tailwinda. Wzorzec obejmuje tylko wartości (np. `-\[[0-9#]`),
  żeby nie łapać `data-[state=open]:` ani `aria-[...]`. Reguła jest też w
  `BUGBOT.md`. `kit-ai reload --dry-run` (kit `@62297eb`) nie nadpisuje tego
  pliku.
- Tor rusza po plasterku 0: wtedy `/design-login` i pierwszy `/design-sync`.
  Ewentualny krok budowania tylko na potrzeby synca dodajemy dopiero wtedy, gdy
  sync go wymusi, bez zmiany
  [ADR 0005](adr/0005-pakiety-wspoldzielone-jako-zrodlo.md). Tor nie blokuje
  plasterków.

**Zależności od kita** (`radthenone/ai-instruction-kit-mcp`, wdrożone w #309
jako kit `@49ce17d`):

- **#187 (wdrożone): etykiety stanu.** Issue plasterków
  zakładamy przez `/create-task` z blokiem „Gotowość”. „Gotowe pod `/git-start`”
  oznacza więc `ready-for-agent` albo `ready-for-human`.
- **#188 (wdrożone): reguły frontendu w bundlu.** Te reguły to:
  - tylko tokeny,
  - plik route'a bez API i logiki, sekcje w `features/` aplikacji,
  - domyślny układ w jednej kolumnie,
  - spec layoutu `docs/design/<N>.md`,
  - nowe klucze `design-tokens`, `routes-web` i `routes-mobile` w `.ai/project.md`,
  - kontrola w `/review-frontend`.

  W tym repo: reguła `ui/` w `frontend/web/AGENTS.md` i w overlayu odsyła do
  modułu `stack:frontend:ui-structure`, klucze `design-tokens`, `routes-web` i
  `routes-mobile` są w `.ai/project.md`. ESLint i grep w CI zostają, bo kit pilnuje
  tylko w review.

  Sekcje w `features/` aplikacji wołają hooki z `@olivin/features`
  ([ADR 0033](adr/0033-hooki-orvala-wprost-logika-domeny-w-pakiecie-features.md)),
  a nie odwrotnie.
- **#189 (wdrożone): etykiety `design: layout` i `design: tokens`, dokument
  `docs/agents/design-handoff.md` oraz follow-upy „design layout” w `/night-run`.**
  Sesja designu kończy się specem `docs/design/<N>.md` według formatu z bundla
  (`docs/agents/design-handoff.md`), a ekrany czekające na projekt dostają
  `design: layout`.

**Pytania na grilling plasterka 3** (dostęp gościa do zamówienia,
[ADR 0038](adr/0038-linki-z-maili-na-jedna-domene-webu-auth-kodem.md)):

1. Anulowanie (`pending`/`paid`) i zgłoszenie zwrotu przez gościa. Propozycja
   właściciela: potwierdzenie jednorazowym kodem z maila, bo mechanizm kodów już
   istnieje (logowanie kodem, weryfikacja e-maila).
2. Formularz „Sprawdź zamówienie” (numer zamówienia + e-mail), który nie
   pokazuje zamówienia od razu, tylko wysyła link z tokenem na ten e-mail.
3. Ważność tokenu i jego los po założeniu konta na ten sam e-mail, gdy
   zamówienie przechodzi na konto.
4. Research przed grillingiem: strona statusu zamówienia w Shopify, śledzenie
   zamówień w WooCommerce, „Orders and Returns” w Magento.

**Zadania przed plasterkiem 5** (po stronie właściciela): projekt Firebase z
`google-services.json` i `eas init`.

**Przed wydaniem iOS:**

- Apple Developer Program: konto firmowe z numerem D-U-N-S.
- Klucz APNs i push na iOS.
- Universal links przetestowane na urządzeniu.
- Sign in with Apple, bo wymaga go wytyczna App Store 4.8 przy logowaniu przez
  Google i Facebook.
- TestFlight i publikacja w App Store.

**Zadania przed plasterkiem 2** (po stronie właściciela):

- Wybrać kanał wysyłki bez umowy z przewoźnikiem: pośrednika (Furgonetka,
  [ADR 0027](adr/0027-integracje-zewnetrzne-przez-adapter.md)) albo konto
  firmowe u przewoźnika z cennikiem standardowym.
- Sprawdzić w cenniku wybranego kanału maksymalną kwotę ubezpieczenia
  przesyłki kurierskiej. Jeśli nie pokrywa najdroższych zamówień, ustawić
  górny limit wartości zamówienia na metodzie kurierskiej.
- Sprawdzić, czy kanał ma odbiór za podpisem, i włączyć go dla droższych
  zamówień.

Przy grillingu plasterka 2 trzeba rozstrzygnąć, czy krok „dostawa” z
[ADR 0030](adr/0030-koszyk-po-stronie-backendu-i-kasa-w-czterech-krokach.md)
zostaje, skoro dla każdej strefy jest dokładnie jedna metoda.

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
| Forma rekompensaty przy zwrocie | Najpierw kupon do wysokości zapłaconej kuponem, reszta pieniędzmi; podstawa rozstrzyga tylko o terminie i dopuszczalności | [0031](adr/0031-zwrot-najpierw-kuponem-reszta-pieniedzmi.md) (zastąpił 0015) |
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
sprzedaży ([0031](adr/0031-zwrot-najpierw-kuponem-reszta-pieniedzmi.md)),
z ręczną obsługą odstąpienia przed doręczeniem,
wraz z wyłączeniem odstąpienia dla grawerunku i produktów na zamówienie
([0024](adr/0024-produkt-na-zamowienie-i-para-jako-jedna-pozycja.md)) oraz
zapisem o przejściu ryzyka i procedurze zaginięcia przesyłki
([0028](adr/0028-ubezpieczenie-przesylki-wliczone-nie-do-wyboru.md)).

Do przeglądu prawnika dodatkowo: czy zgoda marketingowa na push jako flaga
spełnia wymogi przepisów o marketingu elektronicznym (Prawo komunikacji
elektronicznej) ([0037](adr/0037-push-przez-expo-z-minimum-tresci.md)).

Do potwierdzenia u księgowości dodatkowo: zwolnienie z kasy fiskalnej dla
sprzedaży wysyłkowej przy płatności przez operatora na rachunek i ewidencji
wiążącej wpłatę z zamówieniem ([0026](adr/0026-dokument-sprzedazy-generowany-raz-na-backendzie.md)).

Decyzje właściciela z 18–19 września 2026 (przegląd całej wizji sklepu)
zapisane w ADR 0022–0029 i w `CONTEXT.md`; ADR 0017 zastąpiony przez 0022.

Grillowanie serii sprzedażowej z 21–22 września 2026: model kasy w
[ADR 0030](adr/0030-koszyk-po-stronie-backendu-i-kasa-w-czterech-krokach.md),
kurs euro jako uzupełnienia ADR 0019 i 0022.
