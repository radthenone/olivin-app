---
status: accepted
supersedes: 0017
---

# Cena składnikowa z automatycznym przeliczeniem po zatwierdzeniu kursu

Cena wariantu wynika ze wzoru, nie z wpisu ręcznego: składnik kruszcowy (masa
kruszcu razy aktywny kurs za gram dla kruszcu i próby) plus otwarta lista
składników kosztowych (robocizna, kamień, rodowanie, oprawa) razy marża
dziedziczona z kategorii i nadpisywalna na wariancie, zaokrąglone w górę do
pełnych złotych. Cena ręczna jest opcjonalna i ma pierwszeństwo — służy
wyprzedaży, nie codziennej wycenie. Kurs kruszcu ma cykl życia: zadanie okresowe
pobiera go jako **zaproponowany**, właściciel **aktywuje** go w panelu i dopiero
wtedy zadanie przelicza zapisane ceny wariantów z tym kruszcem; kurs
niezatwierdzony niczego nie zmienia. Ręczny wpis kursu pozostaje możliwy.

Zastępuje [ADR 0017](0017-cena-reczna-ze-wstepnym-wyliczeniem.md), który
zakładał cenę wpisywaną przez człowieka z automatyczną podpowiedzią. Powód
zmiany: przy katalogu liczonym w setkach wariantów ręczne przecenianie po
każdej zmianie kursu nie skaluje się, a rozbicie wyceny kamieni i wykonania na
nazwane składniki rozwiązuje zastrzeżenie z 0017, że wzór „nie obejmie kamieni”.

## Consequences

Cena jest zapisana w kolumnie, nie liczona przy odczycie — potrzebna do
filtrowania, sortowania i kontroli progu. Próg minimalny to koszt bez marży;
ani cena ręczna, ani żadna promocja nie schodzą poniżej niego, a panel ostrzega
przy próbie. Aktywacja kursu wysyła wiadomość do właściciela i zostaje w
dzienniku zmian panelu. Dostawca kursu jest wymienny przez adapter — patrz
[ADR 0027](0027-integracje-zewnetrzne-przez-adapter.md).

## Uzupełnienie (2026-09-22)

Cykl życia z zaproponowaniem i aktywacją dotyczy wyłącznie kursu kruszcu.
Kurs euro, którym cena złotowa jest przeliczana dla klienta z Unii
([ADR 0019](0019-sprzedaz-do-ue-w-euro-po-polskim-vat.md)), jest odświeżany
co 30 dni i wchodzi w życie bez aktywacji. Cena w euro jest zaokrąglana w górę
do końcówki ,00 albo ,50, a próg minimalny — koszt wariantu bez marży —
obowiązuje także po przeliczeniu: cena w euro nigdy nie spada poniżej kosztu
przeliczonego tym samym kursem.
