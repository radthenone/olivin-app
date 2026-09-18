# Podstawa zwrotu decyduje o dopuszczalnej formie rekompensaty

Forma rekompensaty nie jest wyborem sklepu — wynika z tego, z jakiego tytułu
klient zwraca towar. Zwrot przechowuje więc podstawę w polu `return_reason`,
a nie wyłącznie kwotę.

Przy **odstąpieniu od umowy w terminie ustawowym** oraz przy **reklamacji**
konsumentowi należy się zwrot pieniędzy, co do zasady tym samym sposobem
zapłaty, jakiego użył. Kupon jest dopuszczalny wyłącznie wtedy, gdy klient
wyraźnie się na niego zgodzi i nie wiąże się to dla niego z żadnym kosztem.
Zgoda musi być odnotowana przy zwrocie.

Przy **zwrocie dobrowolnym**, czyli wykraczającym ponad uprawnienia ustawowe,
zasady ustala sklep. Kupon jest tu w pełni dopuszczalny, ponieważ klient
otrzymuje uprawnienie, którego inaczej w ogóle by nie miał.

## Considered Options

Rozważono politykę jednolitą: każdy zwrot realizowany kuponem. Odrzucona —
zapis regulaminu ograniczający ustawowe prawa konsumenta bez rozróżnienia
podstawy jest kandydatem na klauzulę niedozwoloną, co grozi nieważnością zapisu
i postępowaniem przed urzędem ochrony konkurencji i konsumentów. Wygoda modelu
nie równoważy tego ryzyka.

## Consequences

Regulamin musi rozdzielać zwroty ustawowe od dobrowolnych i nie może narzucać
kuponu na te pierwsze. Regulamin zwrotów i kuponów wymaga przeglądu przez
prawnika przed uruchomieniem sprzedaży — jest to dokument tani w przeglądzie
w porównaniu z kosztem klauzuli niedozwolonej.

Bez zapisanej podstawy zwrotu nie da się wykazać, że wydanie kuponu było
dopuszczalne, ani poprawnie rozliczyć podatku — stąd `return_reason` jest polem
obowiązkowym, nie opcjonalnym.

Produkty zindywidualizowane są wyłączone spod prawa odstąpienia, więc przy nich
kupon pozostaje swobodną decyzją sklepu. Dotyczy to w szczególności grawerunku —
patrz [ADR 0018](0018-grawer-jako-opcja-wylaczajaca-zwrot.md). To jedyny
przypadek, w którym polityka wyłącznie kuponowa nie wchodzi w kolizję z ustawą.

Rozróżnienie dotyczy konsumentów. W sprzedaży firmom strony mogą umówić się
inaczej, ale sklep prowadzi wyłącznie sprzedaż konsumencką — patrz
[ADR 0016](0016-sprzedaz-wylacznie-konsumencka.md).

Zastrzeżenie: ten dokument zapisuje decyzję właściciela wraz z jej
uzasadnieniem, nie stanowi porady prawnej.

## Uzupełnienie (2026-09-19)

Terminy: odstąpienie 14 dni (część zapłacona pieniędzmi wraca pieniędzmi,
część zapłacona kuponem — nowym kuponem), reklamacja 2 lata (zawsze
pieniądze), zwrot dobrowolny 30 dni (wartość pozycji jako nowy kupon
zaokrąglony w górę do pełnych 10 zł, z nowym terminem ważności). Wymiana
rozmiaru nie jest osobnym procesem — to zwrot dobrowolny i nowe zamówienie.
Produkt na zamówienie wyłącza odstąpienie tak jak grawer — patrz
[ADR 0024](0024-produkt-na-zamowienie-i-para-jako-jedna-pozycja.md).
