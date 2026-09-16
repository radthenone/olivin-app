# Otwarte decyzje i praca odłożona

Rejestr rozstrzygnięć, które muszą zapaść, zanim powstaną odpowiadające im
fragmenty systemu, oraz pracy świadomie odłożonej. Każda pozycja mówi, czego
dotyczy, co blokuje, kto rozstrzyga, jakie są opcje i dokąd każda z nich
prowadzi.

Ten plik zastępuje zgłoszenia #32–#38, #40, #54 i #57 na trackerze. Przeniesienie
jest celowe: pytania bez odpowiedzi leżały na trackerze miesiącami obok zadań
wykonalnych, przez co lista przestała odróżniać „do zrobienia" od „do
rozstrzygnięcia". Treść merytoryczna nie uległa zmianie — doszły opcje,
konsekwencje i rekomendacja inżynierska.

Gdy decyzja zapadnie, jej uzasadnienie trafia do `docs/adr/`, a pozycja znika
stąd. Gdy praca odłożona rusza, wraca na tracker jako zadanie z zakresem.

**Zastrzeżenie:** rekomendacje przy pozycjach podatkowych są spojrzeniem
inżynierskim na koszt modelu danych, nie poradą podatkową. Rozstrzyga księgowość.

## Stan modelu w chwili pisania

Istotny kontekst dla wszystkich pozycji poniżej: aplikacje `products` i `orders`
są pustymi szkieletami po `startapp`, a pole stawki podatku nie istnieje nigdzie
w kodzie. Nic z tego, co opisano niżej, nie jest jeszcze zbudowane.

Wniosek praktyczny: te decyzje nie blokują startu prac. Blokują wyłącznie
zamodelowanie **polityki**. Model, który nie zamyka żadnej z opcji, kosztuje
dziś jedno pole, a zmiana modelu po wdrożeniu oznacza migrację danych
produkcyjnych.

---

## Podatki i księgowość

Rozstrzyga: księgowość.

### VAT od złota inwestycyjnego

Czy sklep sprzedaje złoto inwestycyjne (sztabki, monety) obok biżuterii?
W Polsce podlega ono zwolnieniu na innych zasadach niż biżuteria.

Blokuje: model domenowy produktu i zamówienia.

| Opcja | Dokąd prowadzi |
| --- | --- |
| Tylko biżuteria | Jedna stawka dla całego katalogu, prosty model, prosta faktura |
| Także złoto inwestycyjne | Zwolnienie przedmiotowe o innej podstawie prawnej, osobna ewidencja, faktura musi wskazywać podstawę zwolnienia, faktura mieszana rozdziela pozycje na dwie grupy |

Rekomendacja: stawka **per wariant** plus flaga zwolnienia, niezależnie od
odpowiedzi. Koszt to jedno pole; odwrócenie po wdrożeniu to migracja danych
i korekty faktur wstecz. Samą politykę ustala księgowość.

### VAT od kuponów powstałych ze zwrotu

Czy użycie kuponu powstałego ze zwrotu to nowa sprzedaż z VAT, czy korekta
pierwotnej transakcji? Rozstrzygnięcie zmienia to, co zapisujemy w momencie
naliczenia rabatu.

Blokuje: implementację kuponów i zwrotów.
Kontekst: [ADR 0011](adr/0011-kupony-zamiast-salda.md).

| Opcja | Dokąd prowadzi |
| --- | --- |
| Korekta pierwotnej transakcji | Kupon wiąże się z pierwotnym zamówieniem, faktura korygująca, raportowanie obniża pierwotną sprzedaż |
| Nowa sprzedaż | Kupon działa jak rabat na nowej transakcji, VAT naliczany normalnie, pierwotna faktura nietknięta |

Rekomendacja: zapisywać **zdarzenia** (`coupon_issued`, `coupon_redeemed`)
z odwołaniem do zamówienia źródłowego, zamiast trzymać samo saldo. Obie
interpretacje da się wtedy wyliczyć z tych samych danych, więc rozstrzygnięcie
księgowości nie wymusi migracji.

### Strategia fakturowania i KSeF

Czy sklep wystawia faktury automatycznie? Czy integrujemy się z systemem
księgowym? Czy KSeF jest wymagany w naszym przypadku i w jakim terminie?

Obszar nieuwzględniony dotąd w żadnym dokumencie projektu.

Blokuje: zakres modułu zamówień i płatności.
Rozstrzyga: decyzja biznesowa plus księgowość.

| Opcja | Dokąd prowadzi |
| --- | --- |
| Wyłącznie sprzedaż konsumencka | KSeF w zasadzie poza zakresem, znacząco prostszy moduł zamówień |
| Także sprzedaż firmom | KSeF obowiązkowy, integracja z API, autoryzacja, obsługa błędów, przechowywanie UPO |
| Fakturowanie przez system zewnętrzny | Mniej kodu u nas, w zamian integracja i koszt licencji |

Rekomendacja: rozstrzygnąć jako pierwszą pozycję z całej listy — najmocniej
zmienia zakres modułu zamówień, a KSeF jest kosztowny. Pytanie rozstrzygające
jest jedno: **czy sprzedajemy firmom na fakturę.** Terminy KSeF przesuwano
wielokrotnie, więc obowiązującą datę należy potwierdzić u księgowości.

---

## Decyzje biznesowe

Rozstrzyga: właściciel produktu.

### Czy ceny są przeliczane od kursu kruszcu

Czy ceny są ustalane ręcznie, czy przeliczane od kursu kruszcu?

Blokuje: model cen i harmonogram zadań.
Powiązane: [ADR 0010](adr/0010-snapshot-ceny-w-pozycji-zamowienia.md).

| Opcja | Dokąd prowadzi |
| --- | --- |
| Ręcznie | Nic nie trzeba dobudowywać |
| Od kursu kruszcu | Źródło kursu wraz z kosztem i SLA, zadanie okresowe, polityka częstotliwości, narzut marży, ryzyko zmiany ceny w trakcie trwania koszyka |

Rekomendacja: start ręcznie, z polem `price_source` (`manual` / `spot`) na
zapas. Uwaga: przy cenach od kursu kopia ceny w pozycji zamówienia przestaje być
formalnością i staje się zabezpieczeniem — koszyk pokazuje cenę aktualną i nie
zamraża jej, więc klient mógłby zapłacić inną niż widział.

### Czy produkty wspierają personalizację

Czy sklep oferuje grawer, dobór kamienia lub wykonanie na zamówienie?

Blokuje: model koszyka, zamówienia i magazynu.

| Opcja | Dokąd prowadzi |
| --- | --- |
| Nie | Wariant pozostaje egzemplarzem magazynowym, prosta rezerwacja stanu |
| Tak | Pozycja koszyka i zamówienia potrzebują pola na parametry personalizacji, magazyn musi odróżniać towar magazynowy od wykonywanego na zamówienie, zmienia się model rezerwacji, zmienia się polityka zwrotów |

Rekomendacja: rozstrzygnąć przed projektowaniem koszyka. To jedyna pozycja
z listy, która zmienia **model magazynu**, a nie dokłada pole. Dla sklepu
jubilerskiego grawer jest na tyle typowy, że domyślną odpowiedzią wydaje się
„tak" — warto to potwierdzić, zanim powstanie model rezerwacji.

### Zakres sprzedaży transgranicznej

Czy sprzedajemy wyłącznie w Polsce?

Blokuje: model pieniędzy, wysyłki i podatku.
Powiązane: [ADR 0009](adr/0009-kwoty-jako-liczby-calkowite.md).

| Opcja | Dokąd prowadzi |
| --- | --- |
| Wyłącznie Polska | Jedna waluta, jedna jurysdykcja podatkowa, proste metody wysyłki |
| Także Unia Europejska | VAT OSS po przekroczeniu progu sprzedaży wysyłkowej, wielowalutowość, stawki per kraj, metody wysyłki, tłumaczenia treści |

Rekomendacja: start wyłącznie w Polsce, ale **waluta zostaje w modelu od
początku**. Typ `Money` jest już parą kwota plus kod waluty, więc to jest
zapewnione — rzecz w tym, żeby nie upraszczać go w trakcie implementacji do
samych groszy.

Rozróżnienie warte odnotowania: katalog ma model tłumaczeń i integrację z
silnikiem tłumaczeń maszynowych, co sugeruje plany wielojęzyczne. Wielojęzyczność
to jednak nie to samo co wielowalutowość i rozliczenia transgraniczne — katalog
może być wielojęzyczny bez sprzedaży poza Polskę.

---

## Decyzje techniczne odłożone świadomie

Obie pozycje mają zapisane uzasadnienie odłożenia i zostają odłożone nadal.
Rekomendacja jest wstępna — wiążąca decyzja zapada, gdy istnieje przedmiot
decyzji.

### Narzędzie testów end-to-end dla aplikacji mobilnej

Testy przeglądarkowe pokrywają wyłącznie aplikację webową. Aplikacja mobilna nie
ma żadnego pokrycia końcowego i żadne narzędzie nie zostało wybrane.

Odłożone do momentu, w którym istnieje przepływ wart pokrycia, czyli po
zbudowaniu kasy. Bez przepływu do przetestowania wybór jest zgadywaniem.

| Kandydat | Dokąd prowadzi |
| --- | --- |
| Maestro | Testy deklarowane w YAML, działa z Expo bez wychodzenia z managed workflow, niski próg wejścia |
| Detox | Większe możliwości, w zamian wymaga bare workflow lub prebuild i znacznie więcej konfiguracji |

Rekomendacja wstępna: Maestro, przy obecnym ustawieniu projektu (Expo managed).

Osobna, pilniejsza obserwacja: w CI nie ma dziś **żadnego** builda ani testu
aplikacji mobilnej. Skutek zobaczyliśmy przy próbie podniesienia Tailwinda do v4
— PR miał trzy zielone bramki, a rozbijał stylowanie pod NativeWindem. Sam smoke
test builda mobile jest wart rozważenia wcześniej niż pełne testy end-to-end.

### Back office: Django admin czy własny panel

Panel obsługi zamówień, magazynu, zwrotów i moderacji opinii.

Odłożone do momentu, w którym zamówienia i zwroty istnieją.

| Opcja | Dokąd prowadzi |
| --- | --- |
| Django admin | Natychmiastowy i darmowy, słabo znosi złożone przepływy pracy takie jak kompletacja zamówienia czy obsługa zwrotu |
| Własny panel | Dowolne przepływy, w zamian drugi interfejs do zbudowania i utrzymania |

Rekomendacja wstępna: Django admin do chwili, aż konkretny przepływ zacznie
przeszkadzać. Wtedy wypycha się poza admina **ten jeden ekran**, nie cały panel.
Odwrócenie jest tanie, więc odkładanie jest właściwe.

---

## Praca odłożona

### Podniesienie Expo z SDK 54 do SDK 57

Zablokowane upstream. Dev Client nie potrafi pobrać bundla z Metro — parser
chunked encoding po stronie React Native desynchronizuje się, chociaż ten sam
strumień pobrany z hosta jest poprawny. Bez działającego bundla nie da się
sprawdzić logowania, stylowania ani tokenów.

Żywym artefaktem tej pracy pozostaje **draft PR #59**, wraz z pełną diagnostyką.
Ta pozycja istnieje po to, żeby blokada była widoczna poza samym PR-em.

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
