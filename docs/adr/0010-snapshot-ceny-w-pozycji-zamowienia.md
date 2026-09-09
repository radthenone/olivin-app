# Pozycja zamówienia przechowuje kopię ceny, nie odwołanie do wariantu

Pozycja zamówienia zawiera skopiowaną nazwę, cenę, stawkę podatku i parametry wariantu z chwili złożenia zamówienia, zamiast odczytywać je przez klucz obcy. Bez tego historia zamówień, faktury i zwroty zaczynają kłamać po każdej zmianie cennika — co w biżuterii, gdzie ceny bywają powiązane z kursem kruszcu, zdarza się regularnie.

## Consequences

Dane są celowo zduplikowane. Odwrócenie wymaga migracji z utratą historii cen.
