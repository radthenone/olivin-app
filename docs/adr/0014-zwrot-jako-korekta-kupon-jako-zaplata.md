# Zwrot jest korektą pierwotnej sprzedaży, a kupon formą zapłaty

Przyjęty zwrot anuluje pierwotną sprzedaż: powstaje faktura korygująca,
a zapłacony od niej podatek jest odzyskiwany. Wydany kupon nie jest wtedy
sprzedażą ani przychodem — jest zobowiązaniem sklepu wobec klienta.

Wykorzystanie kuponu przy kolejnym zakupie to zwyczajna, nowa sprzedaż
z własnym podatkiem, w której kupon pełni rolę formy zapłaty. Dzięki temu
podatek od tej samej wartości płacony jest raz, a nie dwa razy.

Kupony są wydawane wyłącznie klientom indywidualnym. Sprzedaż firmom
rozliczana jest bez nich.

## Considered Options

Rozważono ujęcie alternatywne, w którym użycie kuponu jest nową sprzedażą,
a pierwotna faktura pozostaje nietknięta, kupon zaś działa jak rabat. Odrzucone,
ponieważ przy zwrocie towaru pierwotna transakcja faktycznie nie dochodzi do
skutku i pozostawienie jej w raportowaniu zawyża sprzedaż.

## Consequences

Model zapisuje **zdarzenia** — `coupon_issued` oraz `coupon_redeemed` — wraz
z powiązaniem do zamówienia źródłowego, zamiast przechowywać samo saldo. Bez
tego powiązania nie da się wystawić korekty wstecz ani udowodnić, skąd wzięła
się wartość kuponu.

Kupon wydany w miejsce zwrotu pieniędzy jest dopuszczalny tylko wtedy, gdy
pozwala na to podstawa zwrotu — reguluje to [ADR 0015](0015-podstawa-zwrotu-decyduje-o-formie-rekompensaty.md).
Sama kwalifikacja podatkowa, opisana tutaj, nie przesądza o tym, czy kupon
w ogóle wolno zaproponować.

Kwalifikacja podatkowa pozostaje rozstrzygnięciem księgowości; ten dokument
zapisuje wybrany wariant, nie zastępuje opinii.
