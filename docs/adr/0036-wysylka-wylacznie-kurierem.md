# Wysyłka wyłącznie kurierem

Sklep wysyła zamówienia wyłącznie kurierem, zarówno w Polsce, jak i do pozostałych krajów Unii. Nie ma paczkomatów, punktów odbioru u żadnego przewoźnika ani odbioru osobistego. W kasie nie ma więc wyboru punktu ani mapy, a metoda dostawy wynika ze strefy w adresie dostawy.

Biżuteria to przesyłka mała, a zarazem droga. Kurier daje deklarację wartości, odbiór do rąk własnych i jasną odpowiedzialność przewoźnika, a sklep ponosi ryzyko do chwili wydania przesyłki ([ADR 0028](0028-ubezpieczenie-przesylki-wliczone-nie-do-wyboru.md)). Paczkomaty mogą wrócić jako późniejsze rozszerzenie.

## Considered Options

- **Paczkomaty InPost z Geowidgetem** (research w `docs/research/paczkomat-widget.md`). Odrzucone na start: niższy limit odpowiedzialności, widget w WebView na mobile i dodatkowy stan w koszyku i zamówieniu.
- **Odbiór osobisty.** Odrzucone, bo sklep nie ma miejsca odbioru.

## Consequences

- Z backendu znikają `ShippingMethodKind.PARCEL_LOCKER`, `ShippingMethodKind.PICKUP` i pole `Shipment.pickup_point_code`, wraz z serializerem, adminem, fabrykami i testami.
- Jeśli paczkomaty wrócą, punkt odbioru trafi na koszyk i zamówienie, a nie na przesyłkę.
- Limit wartości zamówienia z ADR 0028 dotyczy teraz metody kurierskiej. Jeśli maksymalne ubezpieczenie wybranego kanału nie pokryje najdroższych zamówień, zamówienia powyżej limitu nie da się złożyć.
