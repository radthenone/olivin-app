# Koszyk po stronie backendu, gość przez token, kasa w czterech krokach

Koszyk każdego klienta — zalogowanego i gościa — żyje w bazie sklepu, nie
w przeglądarce ani w aplikacji. Gość dostaje od backendu losowy token przy
pierwszym dodaniu pozycji i odsyła go w nagłówku z każdym żądaniem; po
zalogowaniu koszyk gościa zostaje scalony z koszykiem konta, a anonimowy
znika. Wycena pozycji (cena wariantu, grawer, para obrączek, przeliczenie na
euro) odbywa się wyłącznie na backendzie — klient pyta o sumę, nie liczy jej
sam.

Kasa ma cztery kroki: koszyk, dane i adres, dostawa, płatność. Zamówienie
powstaje po trzecim kroku w statusie `pending`, z kopią cen i kosztu dostawy,
i dopiero wtedy tworzona jest intencja płatnicza na kwotę z zamówienia
([ADR 0012](0012-payment-intents-z-gotowymi-elementami.md)). Rezerwacja
stanu magazynowego rusza razem z zamówieniem. Nieudana płatność zostawia
zamówienie `pending` do ponownej próby; zamówienie bez zapłaty przez dobę
anuluje się samo. Gość kupuje bez zakładania konta.

## Considered Options

Koszyk w pamięci klienta (localStorage, stan aplikacji), synchronizowany
z backendem dopiero przy kasie — odrzucony: koszyk gościa nie przeżywa zmiany
urządzenia, walidacja stanu i limitów musiałaby być powielona po stronie
klienta, a scalenie przy logowaniu wymagałoby wysłania całej listy pozycji
na serwer i tak.

Sesja Django (`SessionMiddleware`, cookie `sessionid`) jako tożsamość gościa —
odrzucona: uwierzytelnianie działa przez allauth headless z tokenem, więc
sesja dołożyłaby drugi mechanizm stanu, a aplikacja mobilna nie obsługuje
cookies naturalnie. Token wydawany przez backend działa identycznie na webie
i na mobile.

Zamówienie tworzone dopiero po udanej płatności, do tego czasu wszystko
w koszyku — odrzucone: słownik zakłada, że klient anuluje zamówienie
`pending`, więc musi ono istnieć przed zapłatą; intencja płatnicza wymaga
kwoty zamrożonej w chwili złożenia, a koszyk z założenia ceny nie zamraża.

## Consequences

Koszyk i zamówienie mieszkają w jednej aplikacji, bo dzielą reguły pozycji:
grawer jako osobna pozycja ceny ([ADR 0018](0018-grawer-jako-opcja-wylaczajaca-zwrot.md)),
para obrączek jako jedna pozycja z dwoma rozmiarami
([ADR 0024](0024-produkt-na-zamowienie-i-para-jako-jedna-pozycja.md)),
snapshot ceny przy złożeniu ([ADR 0010](0010-snapshot-ceny-w-pozycji-zamowienia.md)).
Osobna aplikacja koszyka ma sens dopiero, gdy koszyk dostanie własne API
poza kasą.

Koszt dostawy jest znany przed intencją płatniczą, więc metoda dostawy musi
być wybrana przed płatnością i skopiowana do zamówienia — stąd kolejność
kroków. Ubezpieczenie przesyłki pozostaje niewidoczne dla klienta, wliczone
w stałą stawkę metody ([ADR 0028](0028-ubezpieczenie-przesylki-wliczone-nie-do-wyboru.md)).

Koszyki gości bez aktywności przez 30 dni są kasowane zadaniem okresowym.
Interfejs kasy (licznik pozycji, rozwijana lista, cztery ekrany) przychodzi
osobno, po serii backendowej — zapisany w rejestrze otwartych decyzji jako
pomysł na przyszłość; kontrakt API każdego biletu backendowego musi tę drogę
zostawić otwartą.
