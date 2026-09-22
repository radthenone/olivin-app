# Olivin

Sklep jubilerski online. Ten dokument jest wyłącznie słownikiem pojęć domeny — nie zawiera decyzji technicznych ani planów. Decyzje mieszkają w `docs/adr/`, plany w specyfikacjach na trackerze.

Nazwy terminów są angielskie, bo tak nazywają się w kodzie. Definicje polskie.

## Katalog

**Product**:
Model biżuterii jako pozycja katalogowa — nazwa, opis, kategoria, materiał, próba kruszcu. Nie ma ceny ani stanu magazynowego. Ma status: szkic (`draft`) albo opublikowany (`published`); tylko opublikowany jest widoczny w sklepie i podlega tłumaczeniu.
_Unikaj_: Item, Article, Towar

**MadeToOrder**:
Cecha produktu wytwarzanego dopiero po złożeniu zamówienia — obrączki ślubne. Taki produkt nie ma stanu magazynowego, ma za to czas realizacji. Jego wariant opisują parametry wykonania: rozmiar, szerokość, profil, próba, kolor kruszcu.
_Unikaj_: Custom, Preorder, Bespoke, Na wymiar

**ProductImage**:
Zdjęcie produktu albo jego wariantu: kolejność w galerii, oznaczenie zdjęcia głównego i opis alternatywny. Zdjęcie przypisane do wariantu pokazuje się po jego wyborze; bez przypisania należy do produktu. Wariantowe zdjęcia różnicują wygląd (kruszec, kamień), nie rozmiar.
_Unikaj_: Photo, Media, Attachment, Obrazek

**Translation**:
Tłumaczenie pola tekstowego katalogu — nazwy, opisu, opisu zdjęcia, nazwy kategorii i kolekcji — z polskiego jako języka źródłowego. Nie obejmuje sluga, który jest jeden, angielski i niezmienny po publikacji. Powstaje automatycznie albo ręcznie; ręczne nigdy nie jest nadpisywane przez automat. Nie dotyczy interfejsu aplikacji, który jest tłumaczony poza bazą.
_Unikaj_: Locale, i18n (to interfejs), Lokalizacja

**ProductVariant**:
Konkretny, kupowalny egzemplarz produktu z własnym SKU, ceną, stawką podatku i stanem magazynowym. Wariant różnicuje rozmiar, długość, kolor kruszcu lub parametry kamienia — jako cechy o zamkniętej liście wartości, nie wolne etykiety. Jedyna rzecz, którą można dodać do koszyka. Na liście produkt reprezentuje jego najtańszy wariant.
_Unikaj_: SKU (jako nazwa modelu), Option, Wariant produktu

**Gemstone**:
Kamień osadzony w wariancie — rodzaj, masa w karatach, opcjonalnie czystość, barwa i szlif — oraz opcjonalny certyfikat laboratorium z numerem i dokumentem do pobrania. Wariant może mieć wiele kamieni albo żadnego. Widoczny dla klienta; to nie jest pozycja kosztowa.
_Unikaj_: Stone (jako nazwa modelu), Diamond, Kamień jako atrybut tekstowy

**Engraving**:
Grawerunek zamawiany do wyrobu. Możliwość jego wykonania jest flagą na produkcie — nie każdy produkt ją ma. Wyceniany osobną pozycją doliczaną do ceny wariantu. Czyni wyrób towarem zindywidualizowanym, co wyłącza ustawowe prawo odstąpienia.
_Unikaj_: Personalization, Customization, Grawer

**Category**:
Węzeł drzewiastej taksonomii katalogu. Produkt należy do jednej kategorii liścia.
_Unikaj_: Section, Type, Dział

**Collection**:
Grupa marketingowa przecinająca kategorie, powiązana z kampanią lub sezonem. Produkt może należeć do wielu kolekcji. Jedyny przekrój katalogu poza kategorią i cechami wariantu — wolnych tagów nie ma.
_Unikaj_: Group, Tag, Kolekcja jako synonim kategorii

## Pieniądze

**Money**:
Para: liczba całkowita w najmniejszej jednostce waluty oraz kod waluty. Nie jest modelem bazodanowym, tylko konwencją obowiązującą wszędzie, gdzie występuje kwota.
_Unikaj_: Amount, Price (jako typ), Kwota

**Price**:
Cena wariantu widziana przez klienta, wyrażona brutto, zapisana przy wariancie. Powstaje z sumy składnika kruszcowego i składników kosztowych powiększonej o marżę i zaokrąglonej w górę do pełnych złotych; cena ręczna, jeśli ustawiona, ma pierwszeństwo. Kwota netto i podatek są z niej wyliczane, nie przechowywane osobno.
_Unikaj_: Cost, Value, Cennik

**MetalRate**:
Kurs kruszcu dla danej próby: cena za gram z datą i źródłem. Ma cykl życia: zaproponowany, aktywny, zarchiwizowany. Tylko aktywacja przez właściciela zmienia ceny wariantów zawierających ten kruszec; proponowany kurs niczego nie zmienia.
_Unikaj_: GoldPrice, Rate, Kurs (bez wskazania kruszcu)

**CostComponent**:
Nazwana pozycja kosztu wykonania wariantu niezależna od kursu kruszcu: robocizna, kamień, rodowanie, oprawa. Lista otwarta, bez z góry ustalonych rodzajów.
_Unikaj_: Fee, Surcharge, Dodatek

**Margin**:
Narzut na koszt wariantu, procentowy albo kwotowy, dziedziczony z kategorii i nadpisywalny na wariancie.
_Unikaj_: Markup, Profit

**Cost floor**:
Koszt wariantu bez marży — suma składnika kruszcowego i składników kosztowych. Ani cena ręczna, ani żadna promocja nie schodzą poniżej niego.
_Unikaj_: MinPrice, Floor, Próg (bez określenia)

**VatRate**:
Stawka podatku od towarów i usług przypisana do wariantu — to on jest kupowany
i nosi własną cenę. Zwolnienie, którym objęte jest złoto inwestycyjne, nie jest
stawką zerową, tylko osobną flagą wraz z podstawą prawną.
_Unikaj_: Tax, TaxRate

## Koszyk i zamówienie

**Cart**:
Zbiór wariantów wybranych przez klienta przed złożeniem zamówienia, przechowywany na backendzie dla każdego klienta — web i mobile. Należy do użytkownika albo do gościa identyfikowanego tokenem koszyka wydanym przez backend, nigdy do obu. Przy logowaniu koszyk gościa jest scalany z koszykiem konta, a token gościa przestaje działać.
_Unikaj_: Basket, Bag, Koszyk zakupowy

**CartItem**:
Pozycja koszyka: wariant, ilość i parametry personalizacji. Nie zamraża ceny — koszyk pokazuje cenę aktualną. Dwie pozycje na ten sam wariant z różnym grawerunkiem to dwie różne pozycje; nie wolno ich scalić. Para obrączek to jedna pozycja z dwoma egzemplarzami o osobnych rozmiarach i osobnym albo wspólnym grawerunkiem.
_Unikaj_: LineItem, CartLine

**Order**:
Zamówienie złożone przez klienta — zalogowanego albo gościa podającego e-mail i adres; zamówienia gościa zostają podpięte do konta założonego później na ten sam e-mail. Powstaje na początku kroku płatności — przed zapłatą — w statusie `pending`, a zdarzenie od operatora przenosi je do `paid`; nieopłacone wygasa samo. Niemutowalne co do treści: zawiera kopię kosztu dostawy i kursu waluty z chwili złożenia; zmienia się wyłącznie jego status. Klient sam anuluje tylko zamówienie `pending` albo `paid`; później wyłącznie przez zwrot.
_Unikaj_: Purchase, Transaction, Sale

**ExchangeRate**:
Kurs złotego do euro z Narodowego Banku Polskiego, odświeżany co 30 dni i działający bez ręcznej aktywacji, użyty do pokazania cen i pobrania zapłaty w euro od klienta z kraju Unii. Cena w euro jest zaokrąglana w górę do końcówki ,00 albo ,50 i nigdy nie schodzi poniżej kosztu wariantu. Ceny źródłowe są zawsze w złotych.
_Unikaj_: Rate, Currency, Przelicznik

**OrderItem**:
Pozycja zamówienia zawierająca kopię nazwy, ceny, stawki podatku i parametrów wariantu z chwili złożenia zamówienia.
_Unikaj_: OrderLine, LineItem

**Order status**:
Etap cyklu życia zamówienia: `pending`, `paid`, `in_production`, `packed`, `shipped`, `delivered`, `cancelled`, `returned`. Etap `in_production` występuje tylko, gdy zamówienie zawiera produkt wytwarzany na zamówienie. Przejścia są jednokierunkowe poza anulowaniem.
_Unikaj_: State, Stage, Etap

## Płatności

**Payment**:
Odpowiednik pojedynczej próby zapłaty po stronie sklepu, powiązany z identyfikatorem u operatora płatności.
_Unikaj_: Transaction, Charge, Płatność jako synonim zamówienia

**WebhookEvent**:
Zapisane zdarzenie otrzymane od operatora płatności, przechowywane po to, by to samo zdarzenie nie zostało przetworzone dwukrotnie.
_Unikaj_: Event, Notification, Callback

## Promocje

**Promotion**:
Rabat obniżający cenę pozycji przed podatkiem: procentowy albo kwotowy, z zakresem (produkty, kolekcje, kategorie albo cały katalog), okresem obowiązywania, opcjonalnym kodem i opcjonalnym warunkiem członkostwa. Na jedną pozycję działa najwyżej jedna promocja — najkorzystniejsza dla klienta. Nigdy nie schodzi poniżej kosztu wariantu. Może mieć limit użyć na klienta, limit globalny i minimalną wartość koszyka. Nie jest formą zapłaty — tym jest `Coupon`.
_Unikaj_: Discount, Sale, Kupon rabatowy, Kod

**PromotionRedemption**:
Fakt zastosowania promocji w konkretnym zamówieniu wraz z naliczoną kwotą.
_Unikaj_: Usage, PromotionUse

**Membership**:
Poziom klienta: zwykły albo premium. Premium nadawane automatycznie i bezterminowo, gdy suma kwot faktycznie zapłaconych za dostarczone zamówienia — po rabatach, bez wysyłki, bez zwróconych — przekroczy próg. Stały rabat premium jest zwykłą `Promotion` z warunkiem członkostwa, nie osobnym mechanizmem.
_Unikaj_: Tier, Level, VIP, Subskrypcja

## Kupony i zwroty

**Coupon**:
Jednorazowy voucher o nominale z listy (wielokrotność 10 zł), ważny 12 miesięcy, z kodem nadawanym wyłącznie przez sklep. Powstaje z kampanii marketingowej albo z przyjętego zwrotu. W tym sklepie nie istnieje saldo doładowywane przez klienta — kupon jest jedyną formą wartości do wykorzystania w sklepie. Wydawany wyłącznie klientom indywidualnym. Przy zakupie jest formą zapłaty za towar — nie za wysyłkę — naliczaną po promocjach; niewykorzystana część nominału przepada.
_Unikaj_: Voucher, GiftCard, Credit, Saldo, Rabat

**CouponRedemption**:
Fakt użycia kuponu w konkretnym zamówieniu wraz z faktycznie naliczoną kwotą.
_Unikaj_: Usage, CouponUse

**ReturnRequest**:
Zgłoszenie zwrotu towaru przez klienta, oczekujące na rozpatrzenie. Forma
rekompensaty po przyjęciu towaru zależy od `ReturnReason`, nie jest z góry
kuponem.
_Unikaj_: RMA, Refund, Reklamacja

**ReturnReason**:
Podstawa zwrotu: odstąpienie ustawowe (14 dni; część zapłacona pieniędzmi wraca
pieniędzmi, część zapłacona kuponem — nowym kuponem; wyłączone dla grawerunku
i produktów na zamówienie), reklamacja (2 lata, zawsze pieniądze) albo zwrot
dobrowolny ponad uprawnienia ustawowe (30 dni; wartość pozycji jako nowy kupon
zaokrąglony w górę do pełnych 10 zł, z nowym terminem ważności). Rozstrzyga,
czy wolno wydać kupon, czy należy się zwrot pieniędzy. Pole obowiązkowe — bez
niego nie da się wykazać dopuszczalności kuponu ani rozliczyć podatku.
_Unikaj_: Reason, ReturnType, Powód

## Magazyn

**InventoryItem**:
Stan magazynowy wariantu: ilość dostępna i ilość zarezerwowana. Wariant bez stanu pozostaje widoczny jako niedostępny — nie znika i nie staje się produktem na zamówienie; przy stanie do trzech sztuk sklep pokazuje „ostatnie sztuki”.
_Unikaj_: Stock, Inventory, Magazyn

**StockMovement**:
Pojedyncza zmiana stanu magazynowego wraz z przyczyną. Stan jest sumą ruchów, nie polem nadpisywanym.
_Unikaj_: Adjustment, StockChange

**Reservation**:
Czasowe wyłączenie ilości wariantu z dostępności na czas trwania płatności — 30 minut od rozpoczęcia zapłaty. Wygasa, jeśli płatność nie dojdzie do skutku; zamówienie bez zapłaty przez dobę zostaje anulowane. Nie dotyczy produktów na zamówienie.
_Unikaj_: Hold, Lock, Blokada

## Wysyłka

**ShippingMethod**:
Sposób dostawy — paczkomat, kurier, odbiór osobisty, przesyłka do Unii — ze stałą ceną dla strefy (Polska albo Unia), wspólnym dla sklepu progiem darmowej dostawy i górną wartością zamówienia, powyżej której metoda jest niedostępna. Ubezpieczenie jest zawsze wliczone w stawkę; klient go nie wybiera. Koszt dostawy klient zawsze płaci pieniędzmi, nigdy kuponem.
_Unikaj_: Delivery, Carrier, Dostawa

**Shipment**:
Konkretna przesyłka wysłana w ramach zamówienia: numer śledzenia, wartość zadeklarowana przewoźnikowi oraz — dla paczkomatu — kod punktu odbioru. Dla produktu na zamówienie powstaje dopiero po zakończeniu produkcji.
_Unikaj_: Delivery, Parcel

## Dokumenty sprzedaży

**SalesDocument**:
Dokument wystawiony do zamówienia: potwierdzenie zamówienia (zawsze), faktura imienna dla konsumenta (gdy poda dane) albo korekta (przy przyjętym zwrocie). Numerowany ciągle w obrębie rodzaju i roku. Powstaje raz, po stronie sklepu, po opłaceniu zamówienia; klient wyłącznie go pobiera.
_Unikaj_: Invoice (jako nazwa ogólna), Receipt, Paragon

## Opinie

**Review**:
Ocena od 1 do 5 z opcjonalnym krótkim komentarzem, bez zdjęć. Wymaga dostarczonego zamówienia z tym produktem i moderacji przed publikacją; jedna na klienta na produkt, edycja wraca do moderacji.
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

**Favorite**:
Produkt zapisany przez zalogowanego klienta jako lubiany; lista bez limitu, wspólna dla wszystkich jego urządzeń. Gość trzyma taką listę wyłącznie u siebie w aplikacji; przy logowaniu zostaje scalona z listą konta. Dotyczy produktu, nie wariantu.
_Unikaj_: Wishlist, Like, Ulubiony wariant

**Watch**:
Jednorazowa prośba zalogowanego klienta o powiadomienie, gdy konkretny wariant wróci na stan albo stanieje. Wygasa po wysłaniu powiadomienia. Dotyczy wariantu, bo to on ma stan i cenę; produkt na zamówienie można obserwować tylko pod kątem ceny. Komunikat jest marketingowy — podlega preferencjom powiadomień.
_Unikaj_: Subscription, Alert, Obserwowany produkt

**Account anonymisation**:
Usunięcie konta na życzenie klienta: dane osobowe zostają wymazane, konto zablokowane, listy i urządzenia skasowane, a zamówienia i dokumenty sprzedaży pozostają w formie bezosobowej przez okres wymagany prawem podatkowym. Niedostępne, dopóki trwa niedostarczone zamówienie. Eksport danych odbywa się na wniosek, poza aplikacją.
_Unikaj_: Delete account, Hard delete, Kasowanie konta

## Komunikacja

**Notification**:
Zdarzenie zapisane dla klienta — z rodzajem, treścią i znacznikiem odczytania — widoczne w aplikacji i rozsyłane kanałami: push i e-mail. Transakcyjne (status zamówienia, dokument gotowy, zwrot) docierają zawsze; marketingowe (promocje, obserwowane) tylko za zgodą.
_Unikaj_: Message, Alert, Push (jako nazwa zdarzenia)

**NotificationPreference**:
Zgoda klienta na komunikaty marketingowe, osobno dla każdego kanału. Nie obejmuje komunikatów transakcyjnych.
_Unikaj_: Settings, Opt-in (jako model)

**PushDevice**:
Urządzenie klienta zarejestrowane do powiadomień push — jedno konto może mieć wiele.
_Unikaj_: Token, Device (bez określenia)

**NewsletterSubscription**:
Adres e-mail zapisany do wiadomości marketingowych bez konta, aktywny dopiero po potwierdzeniu linkiem. Każda wiadomość pozwala się wypisać bez logowania. Po założeniu konta na ten adres subskrypcja przechodzi w preferencje konta. Ogłoszenie promocji trafia do klientów z kontem i zgodą oraz do potwierdzonych subskrypcji, bez powtórzeń.
_Unikaj_: Mailing list, Lead, Kontakt

**Consent**:
Wersjonowana zgoda klienta albo gościa na regulamin, politykę prywatności lub komunikację marketingową, z datą. Nowa wersja dokumentu wymaga ponownej akceptacji. Zgody na pliki cookie żyją wyłącznie w przeglądarce i nie są tu zapisywane.
_Unikaj_: Agreement, Terms accepted (jako flaga), Cookie consent
