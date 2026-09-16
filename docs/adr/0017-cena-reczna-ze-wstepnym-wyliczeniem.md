# Cena ustalana ręcznie, ze wstępnym wyliczeniem od próby i kursu kruszcu

Cenę wariantu ustala człowiek. Wartość wyrobu jubilerskiego nie wynika z samej
masy kruszcu — bursztyn, brylant czy jakość wykonania podnoszą ją w sposób,
którego nie da się wyliczyć ze wzoru.

System wylicza natomiast **cenę wstępną**, podpowiadaną przy wprowadzaniu
wariantu: masa razy próba razy stawka za gram danego kruszcu. Osoba
wprowadzająca przyjmuje tę wartość albo podnosi ją o wycenę kamieni i materiału.

Stawki za gram złota i srebra są konfigurowalne w panelu administracyjnym.
Obok nich przechowywany jest **próg minimalny** — cena wariantu nie może zejść
poniżej wartości wynikającej z progu, co zabezpiecza przed sprzedażą poniżej
wartości kruszcu przy pomyłce we wprowadzaniu.

## Considered Options

Rozważono ceny przeliczane automatycznie od bieżącego kursu kruszcu. Odrzucone:
wymagałoby źródła kursu wraz z jego kosztem i umową o poziomie usług, zadania
okresowego oraz polityki częstotliwości, a mimo to nie objęłoby wyceny kamieni,
która i tak wymaga człowieka. Automat rozwiązywałby mniejszą część problemu niż
ta, którą by wprowadzał.

## Consequences

Kurs kruszcu wpływa na podpowiedź i na próg, nigdy bezpośrednio na cenę
sprzedaży. Zmiana stawki za gram nie przecenia katalogu samoczynnie — istniejące
ceny pozostają, dopóki człowiek ich nie zmieni.

Cena widziana przez klienta jest zamrażana w pozycji zamówienia w chwili
składania zamówienia, zgodnie z [ADR 0010](0010-snapshot-ceny-w-pozycji-zamowienia.md).
Koszyk pokazuje cenę aktualną i jej nie zamraża, więc zamrożenie przy składaniu
zamówienia jest tym, co gwarantuje, że klient zapłaci cenę, którą zaakceptował.

Stawka za gram i próg to dane konfiguracyjne z historią zmian, nie stałe
w kodzie. Wymagają ekranu w panelu administracyjnym.
