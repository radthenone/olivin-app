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

### Interfejs kasy na webie i mobile

Seria sprzedażowa (#144–#157) buduje wyłącznie backend: modele, panel, API
i testy. Interfejs kasy przychodzi po niej, gdy powstanie interfejs katalogu,
a klient Orval i MSW dostaną stabilne API. Zapisany kierunek: ikonka koszyka
z licznikiem pozycji, rozwijana lista, pełny widok koszyka jako krok pierwszy,
cztery ekrany kasy (koszyk → dane i adres → dostawa → płatność) z arkuszem
operatora wysuwanym od dołu na mobile i osadzonym elementem na webie
([ADR 0012](adr/0012-payment-intents-z-gotowymi-elementami.md),
[ADR 0030](adr/0030-koszyk-na-backendzie-gosc-przez-token-kasa-w-czterech-krokach.md)).
Każdy bilet backendowy niesie sekcję „kontrakt API musi umożliwić", żeby tej
drogi nie zamknąć. Tracker: #158.

### Świadomie poza zakresem pierwszej wersji

Zapisane, żeby nie wracały jako „a może by”: waluty poza złotym i euro,
marketplace z wieloma sprzedawcami, program poleceń, raty i odroczone
płatności, konfigurator 3D z wyceną na żywo, czat i wsparcie na żywo,
własne zdarzenia analityczne z aplikacji mobilnej, adapter kursu kruszcu
(do czasu wyboru dostawcy kurs wpisuje się ręcznie). Raty i polecenia mają
sens po pierwszym roku sprzedaży.

Kolejność platform: web i Android równolegle, iOS po domknięciu narzędzi
EAS (#94).

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
sprzedaży ([0015](adr/0015-podstawa-zwrotu-decyduje-o-formie-rekompensaty.md)),
wraz z wyłączeniem odstąpienia dla grawerunku i produktów na zamówienie
([0024](adr/0024-produkt-na-zamowienie-i-para-jako-jedna-pozycja.md)) oraz
zapisem o przejściu ryzyka i procedurze zaginięcia przesyłki
([0028](adr/0028-ubezpieczenie-przesylki-wliczone-nie-do-wyboru.md)).

Do potwierdzenia u księgowości dodatkowo: zwolnienie z kasy fiskalnej dla
sprzedaży wysyłkowej przy płatności przez operatora na rachunek i ewidencji
wiążącej wpłatę z zamówieniem ([0026](adr/0026-dokument-sprzedazy-generowany-raz-na-backendzie.md)).

Decyzje właściciela z 18–19 września 2026 (przegląd całej wizji sklepu)
zapisane w ADR 0022–0029 i w `CONTEXT.md`; ADR 0017 zastąpiony przez 0022.
