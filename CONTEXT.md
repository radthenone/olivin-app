# Olivin

Sklep jubilerski online. Ten dokument jest wyłącznie słownikiem pojęć domeny — nie zawiera decyzji technicznych ani planów. Decyzje mieszkają w `docs/adr/`, plany w specyfikacjach na trackerze.

Nazwy terminów są angielskie, bo tak nazywają się w kodzie. Definicje polskie.

## Katalog

**Product**:
Model biżuterii jako pozycja katalogowa — nazwa, opis, kategoria, materiał, próba kruszcu. Nie ma ceny ani stanu magazynowego.
_Unikaj_: Item, Article, Towar

**ProductVariant**:
Konkretny, kupowalny egzemplarz produktu z własnym SKU, ceną i stanem magazynowym. Wariant różnicuje rozmiar, długość, kolor kruszcu lub parametry kamienia. Jedyna rzecz, którą można dodać do koszyka.
_Unikaj_: SKU (jako nazwa modelu), Option, Wariant produktu

**Category**:
Węzeł drzewiastej taksonomii katalogu. Produkt należy do jednej kategorii liścia.
_Unikaj_: Section, Type, Dział

**Collection**:
Grupa marketingowa przecinająca kategorie, powiązana z kampanią lub sezonem. Produkt może należeć do wielu kolekcji.
_Unikaj_: Group, Tag, Kolekcja jako synonim kategorii

## Pieniądze

**Money**:
Para: liczba całkowita w najmniejszej jednostce waluty oraz kod waluty. Nie jest modelem bazodanowym, tylko konwencją obowiązującą wszędzie, gdzie występuje kwota.
_Unikaj_: Amount, Price (jako typ), Kwota

**Price**:
Cena wariantu widziana przez klienta, wyrażona brutto. Kwota netto i podatek są z niej wyliczane, nie przechowywane osobno.
_Unikaj_: Cost, Value, Cennik

**VatRate**:
Stawka podatku od towarów i usług przypisana do produktu.
_Unikaj_: Tax, TaxRate

## Koszyk i zamówienie

**Cart**:
Zbiór wariantów wybranych przez klienta przed złożeniem zamówienia. Należy do użytkownika albo do sesji gościa.
_Unikaj_: Basket, Bag, Koszyk zakupowy

**CartItem**:
Pozycja koszyka: wariant i ilość. Nie zamraża ceny — koszyk pokazuje cenę aktualną.
_Unikaj_: LineItem, CartLine

**Order**:
Zamówienie złożone przez klienta. Niemutowalne co do treści; zmienia się wyłącznie jego status.
_Unikaj_: Purchase, Transaction, Sale

**OrderItem**:
Pozycja zamówienia zawierająca kopię nazwy, ceny, stawki podatku i parametrów wariantu z chwili złożenia zamówienia.
_Unikaj_: OrderLine, LineItem

**Order status**:
Etap cyklu życia zamówienia: `pending`, `paid`, `packed`, `shipped`, `delivered`, `cancelled`, `returned`. Przejścia są jednokierunkowe poza anulowaniem.
_Unikaj_: State, Stage, Etap

## Płatności

**Payment**:
Odpowiednik pojedynczej próby zapłaty po stronie sklepu, powiązany z identyfikatorem u operatora płatności.
_Unikaj_: Transaction, Charge, Płatność jako synonim zamówienia

**WebhookEvent**:
Zapisane zdarzenie otrzymane od operatora płatności, przechowywane po to, by to samo zdarzenie nie zostało przetworzone dwukrotnie.
_Unikaj_: Event, Notification, Callback

## Kupony i zwroty

**Coupon**:
Voucher o określonej wartości lub procencie rabatu. Powstaje z kampanii marketingowej albo z przyjętego zwrotu. W tym sklepie nie istnieje saldo doładowywane przez klienta — kupon jest jedyną formą wartości do wykorzystania w sklepie.
_Unikaj_: Voucher, GiftCard, Credit, Saldo

**CouponRedemption**:
Fakt użycia kuponu w konkretnym zamówieniu wraz z faktycznie naliczoną kwotą.
_Unikaj_: Usage, CouponUse

**ReturnRequest**:
Zgłoszenie zwrotu towaru przez klienta, oczekujące na rozpatrzenie. Po akceptacji i przyjęciu towaru powstaje kupon.
_Unikaj_: RMA, Refund, Reklamacja

## Magazyn

**InventoryItem**:
Stan magazynowy wariantu: ilość dostępna i ilość zarezerwowana.
_Unikaj_: Stock, Inventory, Magazyn

**StockMovement**:
Pojedyncza zmiana stanu magazynowego wraz z przyczyną. Stan jest sumą ruchów, nie polem nadpisywanym.
_Unikaj_: Adjustment, StockChange

**Reservation**:
Czasowe wyłączenie ilości wariantu z dostępności na czas trwania płatności. Wygasa, jeśli płatność nie dojdzie do skutku.
_Unikaj_: Hold, Lock, Blokada

## Wysyłka

**ShippingMethod**:
Sposób dostawy wraz z zasadami wyceny.
_Unikaj_: Delivery, Carrier, Dostawa

**Shipment**:
Konkretna przesyłka wysłana w ramach zamówienia, z numerem śledzenia.
_Unikaj_: Delivery, Parcel

## Opinie

**Review**:
Ocena i komentarz klienta do produktu, wymagające zweryfikowanego zakupu oraz moderacji przed publikacją.
_Unikaj_: Rating, Comment, Feedback

## Konto

**User**:
Konto uwierzytelniania — tożsamość, poświadczenia, metody logowania.
_Unikaj_: Account, Customer (to nie to samo)

**Profile**:
Dane osobowe i preferencje powiązane z użytkownikiem.
_Unikaj_: UserInfo, Details

**Address**:
Adres dostawy lub rozliczeniowy należący do profilu.
_Unikaj_: Location, Destination
