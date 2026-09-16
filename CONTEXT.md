# Olivin

Sklep jubilerski online. Ten dokument jest wyłącznie słownikiem pojęć domeny — nie zawiera decyzji technicznych ani planów. Decyzje mieszkają w `docs/adr/`, plany w specyfikacjach na trackerze.

Nazwy terminów są angielskie, bo tak nazywają się w kodzie. Definicje polskie.

## Katalog

**Product**:
Model biżuterii jako pozycja katalogowa — nazwa, opis, kategoria, materiał, próba kruszcu. Nie ma ceny ani stanu magazynowego.
_Unikaj_: Item, Article, Towar

**ProductVariant**:
Konkretny, kupowalny egzemplarz produktu z własnym SKU, ceną, stawką podatku i stanem magazynowym. Wariant różnicuje rozmiar, długość, kolor kruszcu lub parametry kamienia. Jedyna rzecz, którą można dodać do koszyka.
_Unikaj_: SKU (jako nazwa modelu), Option, Wariant produktu

**Engraving**:
Grawerunek zamawiany do wyrobu. Możliwość jego wykonania jest flagą na produkcie — nie każdy produkt ją ma. Wyceniany osobną pozycją doliczaną do ceny wariantu. Czyni wyrób towarem zindywidualizowanym, co wyłącza ustawowe prawo odstąpienia.
_Unikaj_: Personalization, Customization, Grawer

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
Stawka podatku od towarów i usług przypisana do wariantu — to on jest kupowany
i nosi własną cenę. Zwolnienie, którym objęte jest złoto inwestycyjne, nie jest
stawką zerową, tylko osobną flagą wraz z podstawą prawną.
_Unikaj_: Tax, TaxRate

## Koszyk i zamówienie

**Cart**:
Zbiór wariantów wybranych przez klienta przed złożeniem zamówienia. Należy do użytkownika albo do sesji gościa.
_Unikaj_: Basket, Bag, Koszyk zakupowy

**CartItem**:
Pozycja koszyka: wariant, ilość i parametry personalizacji. Nie zamraża ceny — koszyk pokazuje cenę aktualną. Dwie pozycje na ten sam wariant z różnym grawerunkiem to dwie różne pozycje; nie wolno ich scalić.
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
Voucher o określonej wartości lub procencie rabatu. Powstaje z kampanii marketingowej albo z przyjętego zwrotu. W tym sklepie nie istnieje saldo doładowywane przez klienta — kupon jest jedyną formą wartości do wykorzystania w sklepie. Wydawany wyłącznie klientom indywidualnym. Przy kolejnym zakupie jest formą zapłaty, a nie rabatem.
_Unikaj_: Voucher, GiftCard, Credit, Saldo

**CouponRedemption**:
Fakt użycia kuponu w konkretnym zamówieniu wraz z faktycznie naliczoną kwotą.
_Unikaj_: Usage, CouponUse

**ReturnRequest**:
Zgłoszenie zwrotu towaru przez klienta, oczekujące na rozpatrzenie. Forma
rekompensaty po przyjęciu towaru zależy od `ReturnReason`, nie jest z góry
kuponem.
_Unikaj_: RMA, Refund, Reklamacja

**ReturnReason**:
Podstawa zwrotu: odstąpienie ustawowe, reklamacja albo zwrot dobrowolny ponad
uprawnienia ustawowe. Rozstrzyga, czy wolno wydać kupon, czy należy się zwrot
pieniędzy. Pole obowiązkowe — bez niego nie da się wykazać dopuszczalności
kuponu ani rozliczyć podatku.
_Unikaj_: Reason, ReturnType, Powód

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
