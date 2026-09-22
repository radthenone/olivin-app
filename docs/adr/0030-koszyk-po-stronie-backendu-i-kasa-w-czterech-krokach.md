# Koszyk po stronie backendu, gość z tokenem, kasa w czterech krokach

Koszyk każdego klienta — zalogowanego i gościa — żyje na backendzie, nie w
przeglądarce ani w aplikacji. Gość jest identyfikowany tokenem koszyka, który
wydaje backend przy pierwszym dodaniu pozycji; klient przechowuje wyłącznie ten
token i przesyła go w nagłówku każdego wywołania koszyka. Przy logowaniu albo
rejestracji koszyk gościa jest scalany z koszykiem konta: pozycje o tym samym
wariancie i tych samych parametrach personalizacji sumują ilości, pozostałe
trafiają obok siebie, a token gościa przestaje działać. Wycena pozycji — cena
wariantu, grawer, para obrączek, przeliczenie na euro — odbywa się wyłącznie
na backendzie; klient pyta o sumę, nie liczy jej sam.

Kasa ma cztery kroki w stałej kolejności: **koszyk → dane i adres → dostawa →
płatność**. Każdy krok jest osobnym wywołaniem API i zapisuje swój wynik na
backendzie, więc klient może przerwać i wrócić bez utraty postępu. Metody
dostawy i ich koszt wynikają z adresu i wartości koszyka
([ADR 0028](0028-ubezpieczenie-przesylki-wliczone-nie-do-wyboru.md)), dlatego
krok dostawy następuje po adresie, a płatność po dostawie: intencja płatnicza
([ADR 0012](0012-payment-intents-z-gotowymi-elementami.md)) powstaje z kwotą,
w której koszt dostawy jest już znany i zamrożony. Zamówienie jest tworzone na
początku kroku płatności w statusie `pending`, z kopiami cen, kosztu dostawy
i kursu waluty ([ADR 0010](0010-snapshot-ceny-w-pozycji-zamowienia.md),
[ADR 0019](0019-sprzedaz-do-ue-w-euro-po-polskim-vat.md)); zdarzenie od
operatora przenosi je do `paid`. Zamówienie `pending` bez zapłaty wygasa
i zwalnia rezerwację stanu.

## Considered Options

**Koszyk w przeglądarce i w aplikacji** (pamięć lokalna, wysyłany na backend
dopiero przy składaniu zamówienia) — odrzucony. Ceny, dostępność wariantów
i promocje zmieniają się po stronie sklepu, więc koszyk trzymany u klienta
pokazuje nieaktualne kwoty i wymaga ponownej walidacji całości w kasie. Web
i mobile musiałyby utrzymywać dwie osobne implementacje tej samej logiki, a
koszyk nie przechodziłby między urządzeniami klienta.

**Sesja Django dla gościa** (ciasteczko sesyjne wskazujące na koszyk) —
odrzucona. Aplikacja mobilna nie ma ciasteczek, a uwierzytelnianie jest
bezstanowe ([ADR 0008](0008-uwierzytelnianie-allauth-headless.md)); jeden
mechanizm identyfikacji gościa wspólny dla obu klientów wymaga tokenu
przesyłanego jawnie, nie stanu przypiętego do przeglądarki.

**Zamówienie tworzone dopiero po zapłacie** — odrzucone. Operator zwraca
zdarzenie z identyfikatorem intencji; bez zamówienia istniejącego wcześniej
nie ma czego z nim powiązać, a rezerwacja stanu musiałaby żyć poza modelem
zamówienia.

## Consequences

`Cart` dostaje właściciela: użytkownika **albo** token gościa, nigdy oba.
Token jest losowy, wydawany i unieważniany przez backend; koszyk gościa bez
aktywności przez 30 dni jest kasowany zadaniem okresowym, a przedstawienie
tokenu po scaleniu z kontem zwraca pusty koszyk.

Scalenie przy logowaniu jest jedynym momentem, w którym dwa koszyki stają się
jednym. Pozycje z grawerunkiem nie są sumowane — obowiązuje zasada z
[ADR 0018](0018-grawer-jako-opcja-wylaczajaca-zwrot.md), że różny grawer to
różne pozycje.

Kasa jest sekwencją stanów zapisanych na backendzie, więc każdy krok waliduje
poprzednie: brak adresu blokuje wybór dostawy, brak dostawy blokuje płatność.
Klient przed krokiem płatności widzi pełną kwotę, w tym koszt dostawy — zmiana
adresu po wyborze dostawy cofa kasę do kroku dostawy.

Zamówienie `pending` istnieje zanim pieniądze wpłyną, więc historia zamówień
i panel muszą je odróżniać od zamówień opłaconych; nieopłacone zamówienia
znikają automatycznie po upływie terminu, bez udziału obsługi.

Koszyk i zamówienie mieszkają w jednej aplikacji, bo dzielą reguły pozycji:
grawer jako osobna pozycja ceny, para obrączek jako jedna pozycja z dwoma
rozmiarami ([ADR 0024](0024-produkt-na-zamowienie-i-para-jako-jedna-pozycja.md)),
snapshot ceny przy złożeniu. Osobna aplikacja koszyka ma sens dopiero, gdy
koszyk dostanie własne API poza kasą.

Ekrany kasy dla web i mobile są osobnym zadaniem — zapisane jako pomysł na
przyszłość w rejestrze otwartych decyzji, dopóki backend kasy nie istnieje.
