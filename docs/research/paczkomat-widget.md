# Wybór paczkomatu InPost w kasie — web i mobile

> Zastąpione przez [ADR 0036](../adr/0036-wysylka-wylacznie-kurierem.md): sklep wysyła wyłącznie kurierem.

Research do pozycji 4 w `docs/open-decisions.md` („Widget wyboru paczkomatu na
webie i w React Native”). Stan na 2026-10-14. Stack: Next.js 16.4, Expo SDK 57
/ React Native 0.86.3, backend Django.

## TL;DR

- **Web:** oficjalny **Geowidget v5** (`<inpost-geowidget>`), skrypt i CSS
  ładowane z `geowidget.inpost.pl`. Wymaga **publicznego tokenu** z Managera
  Paczek, przypiętego do domen sklepu.
- **Mobile:** ten sam Geowidget w **`react-native-webview`**, ładowany z
  **naszej własnej strony** (np. `https://<domena>/embed/paczkomat`), a nie
  z HTML-a wstrzykniętego do WebView. Strona przekazuje wybrany punkt przez
  `window.ReactNativeWebView.postMessage`. Natywnej mapy na Points API nie
  budujemy: dużo więcej kodu, a niewiele zyskujemy.
- **Backend:** model wie o paczkomacie (`ShippingMethodKind.PARCEL_LOCKER`,
  `Shipment.pickup_point_code`), ale **kasa nie ma gdzie zapisać wybranego
  punktu** przed powstaniem przesyłki. Brakuje pola na koszyku/zamówieniu
  i walidacji kodu punktu.

## 1. Co już jest w repo

| Element | Miejsce | Uwagi |
|---|---|---|
| Rodzaj metody `parcel_locker` | `backend/src/apps/shipping/models.py` (`ShippingMethodKind`) | Docstring: „Paczkomat wymaga kodu punktu odbioru” |
| `ShippingMethod.max_order_value` | tamże | Limit odpowiedzialności paczkomatu: powyżej niego metoda znika z listy (ADR 0028) |
| `Shipment.pickup_point_code` (`CharField(32)`) | tamże | Wypełniane ręcznie w panelu; to przesyłka, nie kasa |
| `GET /shipping-methods/?order_value=&zone=&currency=` | `apps/shipping/views.py` | Zwraca `kind`, więc frontend wie, kiedy otworzyć mapę |
| Strefy `PL` / `EU`, lista krajów UE | `apps/shipping/services.py` | `zone_for_country()` |
| Snapshot dostawy na zamówieniu | `apps/orders/models/order.py` (`shipping_method`, `shipping_method_name`, `shipping_cost`) | **Brak** pola na punkt odbioru |
| `pickupPointCode` w wygenerowanym kliencie | `frontend/packages/api/generated/apps/orders/orders.zod.ts` | Tylko w odczycie przesyłki |
| `react-native-webview`, `react-native-maps`, `expo-maps` | `frontend/mobile/package.json` | **Nie zainstalowane** |
| CSP na webie | `frontend/web` | Nie znaleziono nagłówka CSP; dodając go, trzeba dopuścić hosty z sekcji 3 |

ADR-y:

- **0027** — przewoźnicy wchodzą przez adapter, a pierwszym przewoźnikiem jest
  InPost ShipX. Żaden identyfikator dostawcy nie trafia do modelu domenowego.
  Etykiety i numery śledzenia są na start wpisywane ręcznie. Kod paczkomatu
  (`WAW01M`) jest adresem dostawy, a nie identyfikatorem integracji, więc
  ADR-u nie łamie. Token Geowidgetu to konfiguracja (zmienna środowiskowa),
  nie model.
- **0030** — kasa ma kroki „koszyk → dane i adres → **dostawa** → płatność”.
  Każdy krok jest zapisany na backendzie, a zmiana adresu cofa kasę do kroku
  dostawy. Wybór paczkomatu należy do kroku 3 i musi być **zapisany na
  backendzie** razem z metodą. Krok płatności musi odrzucić metodę
  `parcel_locker` bez kodu punktu.
- **0028** — paczkomat ma górną wartość zamówienia. Powyżej niej kasa
  w ogóle nie pokazuje mapy.
- **0019** — sprzedaż do UE, stawka zależy od strefy. Dziś metoda `EU` to
  osobny rodzaj „Przesyłka do Unii”, bez punktu odbioru.

## 2. Geowidget v5 — fakty ze źródeł

### Osadzenie

```html
<link rel="stylesheet" href="https://geowidget.inpost.pl/inpost-geowidget.css" />
<script src="https://geowidget.inpost.pl/inpost-geowidget.js" defer></script>
<inpost-geowidget token="PUBLIC_TOKEN" language="pl" config="parcelCollect"
                  onpoint="afterPointSelected"></inpost-geowidget>
```

Jest to custom element. Kod i przetwarzanie są po stronie InPostu, a
integrator tylko linkuje skrypt i podaje konfigurację [1][2].

- Atrybuty: `token` (wymagany, publiczny), `language` (`pl`/`en`/`uk`;
  widget pamięta język ostatnio wybrany przez użytkownika), `config`,
  `onpoint` [1][3].
- Wartości `config`: `parcelCollect` (odbiór opłaconej przesyłki: Paczkomat
  i PaczkoPunkt), `parcelCollectPayment` (pobranie), `parcelCollect247`
  (Paczka w Weekend, punkty 24/7), `parcelSend` (nadanie),
  `parcelCollectInPost` i `parcelCollectPaymentInPost` (tylko punkty InPost,
  `partner_id` 0/33/61) [3]. **Dla nas: `parcelCollect`**. Pobrania nie
  ma, bo płatności idą przez payment intents (ADR 0012).
- Zdarzenia: callback z `onpoint` albo zdarzenie DOM `onpointselect`
  (`event.details`); `inpost.geowidget.init` daje `event.detail.api` [1][3].
  Dokumentacja raz pisze `details`, a raz `detail`. Trzeba to sprawdzić
  w sandboksie. Najpewniejsza ścieżka to
  `api.addPointSelectedCallback(cb)` z `ApiInterface` [4].
- `ApiInterface`: `addPointSelectedCallback`, `changeLanguage`,
  `changePointsType`, `changePosition`, `changeZoomLevel`, `search`,
  `clearSearch`, `hideSearchResult`, `selectPoint`, `showPoint`,
  `showPointDetails` [4].

### Jak działa pod spodem (z kodu `inpost-geowidget.js`)

Pobrałem loader (~106 kB) i sprawdziłem go 2026-10-14. Element tworzy
**iframe** `#geowidget-v5-iframe-render`, którego `src` to
`https://geowidget-app.inpost.pl/...?token=…&configname=…&origin=${window.origin}&language=…&parentId=…`
z `allow="geolocation 'self' …"`. Z iframe'em rozmawia przez `postMessage`
(biblioteka Penpal) i odrzuca wiadomości z innego `origin` niż
`geowidget-app.inpost.pl`.

Wniosek (inferencja): token jest weryfikowany względem `origin` strony
osadzającej. HTML wstrzyknięty do WebView (`source={{ html }}`) ma origin
`null` albo `about:blank`, więc token przypięty do domeny go nie przepuści.
Dlatego w aplikacji mobilnej ładujemy stronę z naszej domeny.

### Dane wybranego punktu (`PointInterface`) [5]

`name` (kod, np. `KRA02APP`), `address { line1, line2 }`,
`address_details` (`city`, `province`, `post_code`, `street`,
`building_number`, `flat_number`, zgodnie z Points API [7]),
`location { latitude, longitude }`, `location_description`,
`opening_hours`, `operating_hours_extended`, `location_247`, `type[]`,
`partner_id`, `image_url`, `easy_access_zone`, `physical_type_*`,
`payment_type`, `virtual`, `apm_doubled`.

**Co zapisujemy na backendzie:** `name` (to jedyna wartość potrzebna
przewoźnikowi i do etykiety ShipX), a do potwierdzenia, maila i dokumentu
sprzedaży także snapshot `address.line1`, `address.line2` i
`location_description`. Adresu z frontu nie bierzemy na wiarę. Backend może
sprawdzić `name` w Points API (sekcja 4) i sam pobrać adres.

### Token, domeny, konto

- Token generuje się w Managerze Paczek: **Moje konto → API → Geowidget →
  Generuj**. Wcześniej muszą być uzupełnione dane firmy, czyli adres i dane
  do faktury [1][2].
- Przy generowaniu podaje się **domeny**, z których będzie używany widget [6].
  Według pomocy platform sklepowych domeny wpisuje się po przecinku, bez
  `https://`. Token wygenerowany dla złej domeny daje błąd „Brak dostępu,
  sprawdź czy token został wygenerowany dla właściwej strony” [9] (źródło
  wtórne, ale spójne z [1]).
- Token jest **publiczny** i ląduje w HTML-u, więc nie jest sekretem.
  Zabezpieczeniem jest lista domen.
- Potrzebne jest **konto firmowe**. Konta prywatne nie mają API [9].
- Do sandboksu z localhost nie podaje się domeny przy generowaniu tokenu [1].

### Sandbox i produkcja

| | Sandbox | Produkcja |
|---|---|---|
| Geowidget | `https://sandbox-easy-geowidget-sdk.easypack24.net` (przykłady `/examples/index.html`) | `https://geowidget.inpost.pl` |
| Manager Paczek (token) | `https://sandbox-manager.paczkomaty.pl` (osobna rejestracja: `/auth/register`) | `https://manager.paczkomaty.pl` |
| Points API (ShipX) | `https://sandbox-api-gateway-pl.easypack24.net/v1/points` | `https://api.inpost.pl/v1/points` |

Źródła: [1][2][7]. Bazowy URL widgetu i token należy trzymać w konfiguracji
(`NEXT_PUBLIC_INPOST_GEOWIDGET_URL`, `NEXT_PUBLIC_INPOST_GEOWIDGET_TOKEN`),
tak samo jak inne integracje z ADR 0027.

### Koszt i licencja

W dokumentacji Geowidgetu ani w opisie generowania tokenu nie znalazłem
żadnej opłaty ani osobnej licencji [1][2][6]. Widget jest dodatkiem do konta
nadawcy w Managerze Paczek. Koszty generują przesyłki według umowy z
InPostem, a cennik dla e-sklepów jest indywidualny. **Nie potwierdzono** w
regulaminie: warto zapytać opiekuna handlowego, czy użycie widgetu w
aplikacji mobilnej (przez WebView) mieści się w warunkach.

### Limity zapytań

Ani dokumentacja Geowidgetu, ani strona Points API nie podają limitów [1][7].
Widget sam odpytuje swoje backendy, więc nasze limity go nie dotyczą.
Przy Points API patrz sekcja 4.

### Dostępność (a11y)

Dokumentacja nie wspomina o dostępności. W loaderze nie ma atrybutów
`aria-`, a iframe dostaje tylko `title="InPost Geowidget App…"`. Treść
iframe'a jest poza naszą kontrolą. Widget ma wyszukiwarkę (adres lub kod
pocztowy) i listę wyników (`search`, `hideSearchResult` [4]), co pomaga
osobom bez myszy, ale **nie jest to audytowana zgodność z WCAG**. Fallback
opisuje sekcja 5.

## 3. Mobile: WebView czy natywna mapa

### Opcja A — Geowidget w `react-native-webview` (rekomendowana)

- `react-native-webview` jest w Expo (`npx expo install react-native-webview`),
  dostępny w Expo Go, na Android i iOS [10]. Oficjalna paczka wspiera tylko
  nową architekturę i wymaga RN ≥ 0.76 [11]. RN 0.86 spełnia ten warunek.
- Schemat:
  1. Next.js wystawia lekką stronę `/embed/paczkomat?lang=pl` (bez layoutu
     sklepu), która osadza `<inpost-geowidget>`.
  2. Callback punktu wysyła
     `window.ReactNativeWebView?.postMessage(JSON.stringify({ name, address, location_description }))`.
     Na webie ta sama strona albo komponent woła handler w React.
  3. Aplikacja: `<WebView source={{ uri }} onMessage={…} geolocationEnabled />`.
     W `onMessage` parsujemy JSON, walidujemy kształt (zod) i robimy
     `PATCH` kroku dostawy w API.
- Zalety: jedna integracja z InPostem, jeden token i domena, aktualne dane
  punktów, filtry InPostu (24/7, typy) za darmo, zero logiki mapy.
- Koszty:
  - Zależność od sieci i od naszej strony.
  - Geolokalizacja w WebView wymaga uprawnień: `expo-location`
    / `NSLocationWhenInUseUsageDescription`, a na Androidzie `geolocationEnabled`.
    Bez nich widget startuje od wyszukiwarki, co jest w porządku.
  - UX „strony w aplikacji”.
  - Wiadomości przychodzące z WebView traktujemy jak niezaufane i
    walidujemy na backendzie.
- `originWhitelist` / `onShouldStartLoadWithRequest` ograniczamy do naszej
  domeny, `geowidget*.inpost.pl` i hostów kafelków mapy.

### Opcja B — natywna mapa (`react-native-maps` / `expo-maps`) na Points API

- Dane: `GET /v1/points` zwraca `name`, `location`, `address_details`,
  `type`, `functions`, `opening_hours`, `location_247` i inne pola, ze
  stronicowaniem (`page`, `per_page`, `total_pages`) [7]. Od 2020 roku API
  zwraca maksymalnie 500 wyników na stronę i domyślnie szuka w promieniu
  50 km [8].
- Autoryzacja: `api.inpost.pl/v1/points` wymaga tokenu ShipX. Bez tokenu
  zwraca `403 Access denied`, co sprawdziłem curlem 2026-10-14. Stary host
  `api-pl-points.easypack24.net/v1/points` odpowiadał bez tokenu (200), ale
  nie ma o nim aktualnej dokumentacji. Nie opierałbym na nim produkcji.
- Konsekwencje:
  - Token ShipX jest **sekretem**, więc nie może trafić do aplikacji.
    Potrzebny jest proxy w Django (`/pickup-points/?near=` z cache), czyli
    nowy adapter, endpoint, cache, testy i kontrakt Orval.
  - Do tego natywna mapa: klucz Google Maps na Androidzie, klastrowanie
    tysięcy punktów, wyszukiwarka adresów (geokodowanie to kolejny dostawca)
    i filtry. Wszystko to dla obu platform.
  - Kilka razy więcej kodu niż opcja A, przy dublowaniu tego, co InPost już
    utrzymuje.
- Kiedy ma sens: gdy WebView okaże się nieakceptowalny (UX, recenzja w
  sklepie, wydajność na słabych Androidach) albo gdy InPost odmówi użycia
  widgetu w aplikacji.

### Opcja C — sama lista bez mapy (fallback, nie główna ścieżka)

Pole „kod pocztowy / miasto” wysyła zapytanie do backendu, a ten zwraca
najbliższe punkty z Points API jako listę. Taki fallback wymaga i tak
proxy z opcji B, tylko bez mapy.

## 4. Walidacja po stronie backendu

Kod punktu przychodzi od klienta, więc backend nie powinien mu ślepo ufać:

- Minimum na start: format (`^[A-Z0-9-]{3,32}$`; obecne `max_length=32`
  wystarcza) i to, że metoda ma `kind == parcel_locker`.
- Docelowo (adapter ShipX z ADR 0027): `GET /v1/points/{name}` sprawdza
  `status == "Operating"`, typ `parcel_locker`/`pop` i bierze adres
  z odpowiedzi, a nie z frontu. ShipX przy tworzeniu przesyłki i tak
  odrzuci nieistniejący `target_point`, więc błąd wyjdzie najpóźniej przy
  nadaniu. Dziś etykiety są ręczne, więc wyszedłby dopiero u obsługi.

Proponowany kształt danych (do decyzji, nie implementacja):

- `Cart.pickup_point_code` + `pickup_point_label` (snapshot `line1, line2`),
  zapisywane w kroku 3 i kopiowane do `Order` przy tworzeniu zamówienia
  `pending` (ADR 0030, ADR 0010: snapshot).
- Zmiana adresu albo metody czyści punkt (ADR 0030: zmiana adresu cofa
  kasę do kroku dostawy).
- `Shipment.pickup_point_code` dostaje wartość z zamówienia zamiast wpisu
  z ręki.

## 5. Dostępność i fallback

- Alternatywa bez mapy: pole tekstowe „Kod paczkomatu” (np. `WAW01M`) obok
  przycisku „Wybierz na mapie”. Część klientów zna swój paczkomat. To spełnia
  wymóg ścieżki bez interakcji z mapą i działa, gdy widget się nie załaduje
  (blokery, awaria InPostu, brak sieci w WebView). Wymaga walidacji z
  sekcji 4. Wariant minimalny (sam format) wystarczy na start.
- Na webie widget ładujemy leniwie, dopiero po wyborze metody
  `parcel_locker` (`next/script` z `strategy="lazyOnload"` albo
  dynamiczny import komponentu). Pokazujemy stan ładowania i błąd z
  odesłaniem do pola tekstowego.
- Po wyborze punktu wyświetlamy go jako tekst (kod + adres) z przyciskiem
  „Zmień”, czytelny dla czytnika ekranu. Mapa jest pomocą, nie jedynym
  nośnikiem informacji.

## 6. Dostawy do UE (ADR 0019)

- Geowidget **v5 PL** pokazuje punkty w Polsce. Istnieje osobny
  **Geowidget International** z atrybutem `country` (PL, BE, IT, FR, LU,
  PT, ES, NL) i językami pl/en/uk/es/fr/pt/it. Sandbox:
  `https://sandbox-global-geowidget-sdk.easypack24.net/inpost-geowidget.js`,
  produkcja: `https://geowidget.inpost-group.com` [12]. Tam `config`
  ma `parcelCollect` dla wszystkich krajów, a reszta opcji jest tylko dla PL.
- Usługa InPost International (PL → BE, FR, ES, NL, LU, PT, IT, AT, HU) to
  osobny produkt w umowie z InPostem. W FR, BE, LU i NL doręcza Mondial
  Relay (źródła wtórne [13]). ADR 0027 zakłada **Furgonetkę** dla zagranicy.
- Dziś kasa ma dla UE rodzaj `eu` („Przesyłka do Unii”, kurier bez punktu).
  **Rekomendacja: na start paczkomat tylko dla strefy PL.** Dla UE zostaje
  kurier. Paczkomaty zagraniczne to osobna decyzja handlowa (umowa InPost
  International albo Furgonetka) i osobny bilet. Wtedy wystarczy podmienić
  host widgetu i dodać `country`, a komponent zostaje.
- Uwaga przy jubilerstwie: limit odpowiedzialności paczkomatu (ADR 0028)
  ogranicza wartość. Przy droższych zamówieniach i tak zostaje kurier.

## 7. Rekomendacja

1. **Web i mobile: Geowidget v5 PL, `config="parcelCollect"`, jedna strona
   `/embed/paczkomat` w Next.js.** Web osadza komponent bezpośrednio, a
   mobile ładuje tę stronę w `react-native-webview` i odbiera punkt przez
   `postMessage`. Jeden token z domeną sklepu (+ `localhost` w sandboksie).
2. Obok mapy pole tekstowe „kod paczkomatu” jako fallback a11y i awaryjny.
3. Backend: pole punktu na koszyku i zamówieniu (snapshot kodu i adresu),
   walidacja formatu w kroku 3, odrzucenie płatności dla `parcel_locker` bez
   punktu. Weryfikacja w Points API dochodzi razem z adapterem ShipX.
4. Natywnej mapy nie robimy. Wracamy do niej, jeśli WebView nie przejdzie
   testów UX na urządzeniach (Maestro, ADR 0020) albo InPost zakaże takiego
   użycia.
5. Paczkomat tylko w strefie PL. UE wymaga osobnej decyzji.

## 8. Otwarte pytania do właściciela

1. **Konto InPost:** czy jest już firmowe konto w Managerze Paczek z
   uzupełnionymi danymi do faktury? Bez niego nie wygenerujemy tokenu,
   nawet sandboksowego (sandbox wymaga osobnej rejestracji).
2. **Domeny:** jaka będzie produkcyjna domena sklepu (i staging), żeby
   przypiąć do niej token?
3. **Limit wartości paczkomatu:** jaka kwota w `max_order_value`? Zależy
   od umowy i ubezpieczenia (ADR 0028).
4. **UE:** czy w ogóle chcemy paczkomaty za granicą? Jeśli tak, przez
   InPost International czy przez Furgonetkę (ADR 0027)?
5. **Warunki użycia:** czy InPost (opiekun handlowy) potwierdza, że widget
   wolno osadzić w aplikacji mobilnej przez WebView i że nie ma opłat?
6. **Paczka w Weekend / tylko punkty InPost:** czy ograniczamy do
   paczkomatów (`parcelCollectInPost`), czy dopuszczamy PaczkoPunkty
   partnerów (sklepy, kioski)? Dla biżuterii z grawerem paczkomat 24/7
   może być bezpieczniejszy.
7. **Lokalizacja w aplikacji:** czy chcemy prosić o uprawnienie do lokalizacji
   (mapa startuje „przy mnie”), czy wystarczy wyszukiwarka?

## Źródła

1. InPost, *Geowidget v5 (PL Market)*. https://dokumentacja-inpost.atlassian.net/wiki/spaces/PL/pages/50069505/Geowidget+v5
2. InPost, *Geowidget v5 ENG (PL Market)*. https://dokumentacja-inpost.atlassian.net/wiki/spaces/PL/pages/58327041
3. InPost, Geowidget TypeDoc (parametry, `config`, zdarzenia). https://geowidget.inpost.pl/docs/ oraz https://geowidget.inpost.pl/docs/interfaces/params.html
4. InPost, `ApiInterface`. https://geowidget.inpost.pl/docs/interfaces/ApiInterface.html
5. InPost, `PointInterface`. https://geowidget.inpost.pl/docs/interfaces/PointInterface.html
6. InPost, *How to Set Up Access to the ShipX API & Geowidget*. https://dokumentacja-inpost.atlassian.net/wiki/spaces/PL/pages/1187086337
7. InPost, *Points (Parcel Locker, ParcelPoint)* — ShipX. https://dokumentacja-inpost.atlassian.net/wiki/spaces/PL/pages/18153493 ; *Display of collection points*: https://dokumentacja-inpost.atlassian.net/wiki/spaces/PL/pages/46465025
8. InPost, *API Points* (zmiany: 500 na stronę, promień 50 km). https://inpost.pl/en/news-api-points
9. Shoper, *Integracja z InPost — kurier i paczkomaty* (źródło wtórne: format domen, komunikat błędu, konto firmowe). https://www.shoper.pl/help/artykul/integracja-z-inpost-kurier-i-paczkomaty
10. Expo, *WebView* (SDK 57). https://docs.expo.dev/versions/latest/sdk/webview/
11. react-native-webview, README. https://github.com/react-native-webview/react-native-webview
12. InPost, *Geowidget International*. https://dokumentacja-inpost.atlassian.net/wiki/spaces/PL/pages/481755145/Geowidget+International
13. Shoper, *InPost International* (wtórne: kraje, Mondial Relay). https://www.shoper.pl/kurierzy/inpost-international

Weryfikacje własne (2026-10-14): `curl` na `https://api.inpost.pl/v1/points`
zwrócił 403 bez tokenu, a `https://api-pl-points.easypack24.net/v1/points`
zwrócił 200 bez tokenu. Analiza `https://geowidget.inpost.pl/inpost-geowidget.js`
pokazała iframe `geowidget-app.inpost.pl` z parametrami `token` i `origin` oraz
komunikację przez `postMessage`.
