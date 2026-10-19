# Research: linki z maili — aplikacja Expo albo web Next.js

Data: 2026-10-14. Dotyczy decyzji przekrojowej nr 6 z `docs/open-decisions.md`
(„Deep linki z maili: universal links, app links i ścieżka awaryjna na web”).

Stack: Expo SDK 57 (`expo ~57.0.23`, `expo-router ~57.0.21`), Android + iOS,
Next.js 16 (`next ^16.4.0`), Django + `django-allauth[headless]>=65.19.7`
w trybie sesyjnym. Źródła są pierwotne (Apple, Android, Expo, allauth, Django,
OWASP, Microsoft, Twilio SendGrid). Stan repo pochodzi z kodu. Wnioski własne
są oznaczone jako **[wniosek]**.

---

## TL;DR

- Jeden adres HTTPS na domenie sklepu (np. `https://olivin.pl/...`) dla weba
  i aplikacji. Jeśli aplikacja jest zainstalowana i domena zweryfikowana, system
  otwiera aplikację. Jeśli nie, link otwiera się w przeglądarce i obsługuje go
  Next.js. Apple i Android opisują dokładnie ten model
  ([Apple: universal links](https://developer.apple.com/documentation/xcode/allowing-apps-and-websites-to-link-to-your-content),
  [Android 12: web intent resolution](https://developer.android.com/about/versions/12/behavior-changes-all)).
  Osobna strona „przekierowań” ani biblioteka nie są potrzebne.
- Next.js serwuje `/.well-known/apple-app-site-association` i
  `/.well-known/assetlinks.json` jako JSON, bez przekierowań. Aplikacja deklaruje
  `ios.associatedDomains` i `android.intentFilters` z `autoVerify: true`.
- Ścieżki URL muszą być identyczne w Next.js (`app/`) i w expo-router (`app/`).
  Dziś się **nie zgadzają**: backend wysyła `/account/reset-password/{key}`,
  a aplikacja ma trasę `/reset-password/[key]`. Web nie ma jeszcze żadnej z
  tych tras (szczegóły w sekcji 1).
- Śledzenie kliknięć w ESP i Microsoft Safe Links zawijają link w cudzą domenę.
  Universal link wtedy nie działa wprost. W mailach transakcyjnych wyłączamy
  śledzenie kliknięć, a strona web musi w pełni obsłużyć każdy link.
- Token w URL: jednorazowy, krótki termin ważności, akcja dopiero po POST
  (nie przy GET), `Referrer-Policy: no-referrer`, usunięcie tokenu z paska
  adresu po odczycie i brak skryptów firm trzecich na tych stronach.
- Na Windowsie bez iPhone'a da się w pełni przetestować Androida (emulator +
  `adb`) i stronę serwera (curl, walidator Google). Universal links na iOS
  wymagają płatnego konta Apple i urządzenia, zob. `docs/research/ios-bez-maca.md`.

---

## 1. Stan repo (2026-10-14)

### Backend — `backend/src/core/settings/components/allauth/headless.py`

```python
HEADLESS_FRONTEND_URLS = {
    "account_confirm_email": "http://localhost:8081/account/verify-email/{key}",
    "account_reset_password": "http://localhost:8081/account/reset-password",
    "account_reset_password_from_key": "http://localhost:8081/account/reset-password/{key}",
    "account_signup": "http://localhost:8081/signup",
    "account_login": "http://localhost:8081/login",
    "account_email_verification_sent": "http://localhost:8081/account/verification-sent",
}
```

- Wartości są zakodowane na sztywno i wskazują na **Expo web dev server
  (`:8081`)**, nie na Next.js (`:3000`). Nie czyta ich żadna zmienna
  środowiskowa, więc produkcja wysłałaby link na `localhost`.
- Klucze `account_login` i `account_email_verification_sent` nie występują
  w przykładzie z dokumentacji allauth. Dokumentacja wymienia
  `account_confirm_email`, `account_reset_password`,
  `account_reset_password_from_key`, `account_signup` i
  `socialaccount_login_error`
  ([allauth: headless configuration](https://github.com/pennersr/django-allauth/blob/main/docs/headless/configuration.rst)).
  **[wniosek]** Pewnie są nieużywane. Nie sprawdzałem tego w kodzie allauth.
- `account/configuration`: `ACCOUNT_EMAIL_VERIFICATION_BY_CODE_ENABLED = True`.
  Allauth: „Controls whether email verification is performed by means of
  following a link in the email (`False`), or by entering a code (`True`)”
  ([allauth: account configuration](https://github.com/pennersr/django-allauth/blob/main/docs/account/configuration.rst)).
  **Weryfikacja e-maila idzie więc kodem, nie linkiem.** Klucz
  `account_confirm_email` jest dziś martwy. Logowanie kodem
  (`ACCOUNT_LOGIN_BY_CODE_ENABLED`) też nie wymaga linku.
- `ACCOUNT_PASSWORD_RESET_BY_CODE_ENABLED` nie jest ustawione (domyślnie
  `False`), więc **reset hasła idzie linkiem**. To jedyny link z allauth,
  który faktycznie trafia do maila.
- `PASSWORD_RESET_TIMEOUT` nie jest ustawione. Domyślnie wynosi 259200 s, czyli
  3 dni ([Django settings](https://docs.djangoproject.com/en/5.2/ref/settings/#password-reset-timeout)).

### Backend — `backend/src/core/settings/components/email.py`

Pozostałe linki z maili wskazują na Next.js. Od #313 nie czytają już
własnych zmiennych środowiskowych. Składa je `FRONTEND_URL` z prefiksem `/pl`,
do czasu wyboru języka z `PreferredLanguage` (ADR 0038):

| Ustawienie | Wartość (z `FRONTEND_URL`) | Token |
|---|---|---|
| `NEWSLETTER_CONFIRM_URL` | `{FRONTEND_URL}/pl/newsletter/confirm/{token}` | UUID `confirmation_token` |
| `NEWSLETTER_UNSUBSCRIBE_URL` | `{FRONTEND_URL}/pl/newsletter/unsubscribe/{token}` | UUID subskrypcji albo `signing.dumps(pk)` konta |
| `CART_URL` | `{FRONTEND_URL}/pl/cart` | brak |
| `NOTIFICATION_PREFERENCES_URL` | `{FRONTEND_URL}/pl/account/notifications` | brak |

Maile o statusie zamówienia (`apps/notifications/services.py`,
`order_status_changed`, `order_paid` itd.) **nie zawierają dziś linku**.

### Mobile — `frontend/mobile`

- `app.config.js`: `scheme: ["olivin", "com.olivin.frontend", fb…]`,
  `ios.bundleIdentifier` i `android.package` mają wartość `com.olivin.frontend`.
  Brakuje `ios.associatedDomains` i `android.intentFilters`, więc universal
  links i app links nie są skonfigurowane.
- Trasy: `app/(auth)/verify-email.tsx` → URL `/verify-email`, a
  `app/(auth)/reset-password/[key].tsx` → URL `/reset-password/:key`. Grupy
  w nawiasach nie tworzą segmentu URL. Ekrany czytają `key` przez
  `useLocalSearchParams`.
- `app/+native-intent.tsx` przepisuje tylko callbacki OAuth (`authredirect`,
  `oauthredirect`, `authorize`). Pozostałe ścieżki przepuszcza bez zmian.
- Brakuje tras `newsletter/*`, `cart` i `account/notifications`.

### Web — `frontend/web`

`app/` zawiera tylko `page.tsx` i `layout.tsx`. Nie ma żadnej trasy, na którą
backend dziś linkuje: ani `/newsletter/confirm/[token]`, ani
`/account/reset-password/[key]`, ani `/.well-known/*`.

**[wniosek]** Rozjazd ścieżek trzeba usunąć niezależnie od wyboru
universal links. Dziś link resetu nie trafi w żaden ekran ani w aplikacji, ani
w Next.js.

---

## 2. Jak system decyduje: aplikacja czy przeglądarka

### iOS — universal links

- „When users tap or click a universal link, the system redirects the link
  directly to your app without routing through the person's default web
  browser or your website. […] one URL works for both your website and your
  app. If the person hasn't installed your app, the system opens the URL in
  their default web browser, allowing your website to handle it.”
  ([Apple](https://developer.apple.com/documentation/xcode/allowing-apps-and-websites-to-link-to-your-content))
- Kliknięcie linku z tej samej domeny w Safari zostaje w Safari. Link z innej
  domeny otwiera aplikację (tamże). Wpisanie URL w pasek adresu nigdy nie
  otwiera aplikacji. Długie przytrzymanie pozwala wybrać „otwórz w aplikacji”
  albo „w przeglądarce”, a system zapamiętuje ten wybór dla domeny
  ([TN3155: Debugging universal links](https://developer.apple.com/documentation/technotes/tn3155-debugging-universal-links)).
- Obsługa universal links w przeglądarkach innych niż Safari zależy od ich
  producenta (TN3155).

### Android — App Links

- „Starting in Android 12 (API level 31), a generic web intent resolves to an
  activity in your app only if your app is approved for the specific domain
  […]. If your app isn't approved for the domain, the web intent resolves to
  the user's default browser app instead.”
  ([Android 12 behavior changes](https://developer.android.com/about/versions/12/behavior-changes-all))
- Zweryfikowane App Links otwierają aplikację bez okna wyboru. Są dostępne od
  Androida 6 na urządzeniach z usługami Google
  ([Android: App Links](https://developer.android.com/training/app-links)).

**[wniosek]** Fallback „brak aplikacji → web” jest wbudowany w oba systemy.
Wystarczy, że ten sam URL działa w Next.js. Nie potrzebujemy strony pośredniej
z wykrywaniem aplikacji ani schematu `olivin://` w mailach. Customowe schematy
w mailach to zły pomysł: bez aplikacji link nie działa wcale.

---

## 3. iOS: `apple-app-site-association` (AASA) i `associatedDomains`

### Plik na serwerze

- Nazwa `apple-app-site-association` bez rozszerzenia, w katalogu `.well-known`.
  „You must host the file using `https://` with a valid certificate and with no
  redirects.” Każda subdomena potrzebuje własnego pliku
  ([Apple: Supporting associated domains](https://developer.apple.com/documentation/xcode/supporting-associated-domains)).
- Od iOS 14 urządzenia nie pobierają pliku z naszego serwera, tylko z CDN
  Apple. CDN pobiera plik „within 24 hours”, a urządzenia sprawdzają aktualizacje
  „approximately once per week after app installation” (tamże).
- Serwer musi wpuszczać każde IP i każdy User-Agent. 301/302 i 403/404 psują
  weryfikację (TN3155). Maksymalny rozmiar to 128 KB
  ([Expo: iOS Universal Links](https://docs.expo.dev/linking/ios-universal-links/)).
- Format: TN3155 każe wybrać **albo** nowy format (`appIDs` + `components`),
  **albo** stary (`appID` + `paths`), i „avoid mixing formats”. Expo zaleca
  odwrotnie: oba formaty naraz, nowy jako pierwszy. **[wniosek]** Wybieramy
  Apple i tylko nowy format. SDK 57 i tak nie wspiera iOS starszych niż 13.

Przykład dla Olivin (`TEAMID` to Apple Team ID; brakuje go w repo):

```json
{
  "applinks": {
    "details": [
      {
        "appIDs": ["TEAMID.com.olivin.frontend"],
        "components": [
          { "/": "/account/reset-password/*", "comment": "Reset hasła" },
          { "/": "/newsletter/*", "comment": "Potwierdzenie i wypis" },
          { "/": "/orders/*", "comment": "Status zamówienia" },
          { "/": "/cart" },
          { "/": "/account/notifications" }
        ]
      }
    ]
  }
}
```

**[wniosek]** Lepiej wymieniać ścieżki jawnie niż dawać `/*`. Wtedy strony
regulaminu, bloga czy płatności zostają w przeglądarce, a dodanie nowej
ścieżki jest świadomą decyzją. Zmiana listy dociera do urządzeń z
opóźnieniem (CDN + tygodniowy cykl), dlatego ścieżki planujemy z wyprzedzeniem.

### Next.js: jak serwować

Plik z `public/` bez rozszerzenia nie dostanie typu `application/json`.
**[wniosek]** Lepszy jest Route Handler, który ustawia nagłówek jawnie
([Next.js: Route Handlers](https://nextjs.org/docs/app/building-your-application/routing/route-handlers)):

```ts
// frontend/web/app/.well-known/apple-app-site-association/route.ts
export const dynamic = "force-static";
export function GET() {
  return Response.json({ applinks: { details: [/* jak wyżej */] } });
}
```

To samo dla `app/.well-known/assetlinks.json/route.ts`. Middleware/proxy
(i18n, auth) nie może przekierowywać `/.well-known/*`. Sprawdzenie po
wdrożeniu: `curl -v https://<domena>/.well-known/apple-app-site-association`
powinno zwrócić 200, `application/json` i zero przekierowań. To samo z
`curl -A "MyAgent-Bot/*"` (TN3155). Oficjalnego przykładu Next.js dla
`.well-known` nie znalazłem. Działanie trzeba potwierdzić curlem.

### Konfiguracja aplikacji

```js
ios: {
  bundleIdentifier: "com.olivin.frontend",
  associatedDomains: ["applinks:olivin.pl"], // bez https://
}
```

Expo: „do not include the protocol (`https`)”
([Expo](https://docs.expo.dev/linking/ios-universal-links/)). Na czas
developmentu Apple pozwala obejść CDN parametrem
`applinks:<domena>?mode=developer` („alternate mode”)
([Apple](https://developer.apple.com/documentation/xcode/supporting-associated-domains)).
Wymaga to włączenia „Associated Domains Development” w Settings > Developer
na urządzeniu (TN3155).

---

## 4. Android: `assetlinks.json` i `intentFilters`

### Plik na serwerze

- `https://<domena>/.well-known/assetlinks.json`, typ `application/json`,
  „must be accessible without any redirects (no 301 or 302 redirects)”, osobny
  plik na każdej domenie z manifestu
  ([Android: configure website associations](https://developer.android.com/training/app-links/configure-assetlinks)).

```json
[
  {
    "relation": ["delegate_permission/common.handle_all_urls"],
    "target": {
      "namespace": "android_app",
      "package_name": "com.olivin.frontend",
      "sha256_cert_fingerprints": ["<SHA256 klucza podpisującego Play>", "<SHA256 klucza EAS/dev>"]
    }
  }
]
```

- Odcisk pobieramy przez `eas credentials -p android` albo z Play Console
  (Release > Setup > App Signing). Tablica przyjmuje kilka odcisków, np. dla
  wariantów i kluczy
  ([Expo: Android App Links](https://docs.expo.dev/linking/android-app-links/)).
  **[wniosek]** Przy Play App Signing klucz z Play różni się od klucza uploadu.
  Trzeba wpisać oba, jeśli testujemy też buildy spoza sklepu.

### Konfiguracja aplikacji

```js
android: {
  package: "com.olivin.frontend",
  intentFilters: [
    {
      action: "VIEW",
      autoVerify: true,
      data: [
        { scheme: "https", host: "olivin.pl", pathPrefix: "/account/reset-password" },
        { scheme: "https", host: "olivin.pl", pathPrefix: "/newsletter" },
        { scheme: "https", host: "olivin.pl", pathPrefix: "/orders" },
      ],
      category: ["BROWSABLE", "DEFAULT"],
    },
  ],
}
```

„Specifying `autoVerify` is required for Android App Links to work correctly.”
Weryfikacja może potrwać „20 seconds or longer”
([Expo](https://docs.expo.dev/linking/android-app-links/)). Na Androidzie 15+
zmiany w `assetlinks.json` mogą się propagować „up to seven days”. Na 14 i
starszych są pobierane zwykle przy instalacji albo aktualizacji
([Android: verify App Links](https://developer.android.com/training/app-links/verify-android-applinks)).

---

## 5. expo-router: obsługa przychodzącego URL

- „Expo Router does not require additional configuration for Universal Links
  and multiple domains.” Każdy przychodzący URL jest dopasowywany do tras
  pliku tak samo jak ścieżka webowa
  ([Expo Router: native intent](https://docs.expo.dev/router/advanced/native-intent/)).
  `https://olivin.pl/account/reset-password/abc` trafi więc do
  `app/.../account/reset-password/[key].tsx`, jeśli taka trasa istnieje.
- `+native-intent.tsx` z `redirectSystemPath({ path, initial })` przepisuje URL
  przed nawigacją. Dokumentacja ostrzega, że `path` nie musi być poprawną
  ścieżką ani URL-em, że funkcja „must not crash” i że działa poza kontekstem
  aplikacji, bez dostępu do stanu auth (tamże). Repo ma już taki plik z
  try/catch, więc tutaj można mapować stare ścieżki na nowe.
- Gdy aplikacja jest już otwarta, zmiany URL obsługuje się w `_layout`
  (`usePathname`) (tamże).

**[wniosek]** Najprostsza droga to **te same ścieżki plików w obu `app/`**:

| Ścieżka URL | Next.js (`frontend/web/app`) | expo-router (`frontend/mobile/app`) |
|---|---|---|
| `/account/reset-password/[key]` | `account/reset-password/[key]/page.tsx` | `(auth)/account/reset-password/[key].tsx` |
| `/newsletter/confirm/[token]` | `newsletter/confirm/[token]/page.tsx` | `newsletter/confirm/[token].tsx` |
| `/newsletter/unsubscribe/[token]` | `newsletter/unsubscribe/[token]/page.tsx` | `newsletter/unsubscribe/[token].tsx` |
| `/orders/[number]` (gdy mail dostanie link) | `orders/[number]/page.tsx` | `(app)/orders/[number].tsx` |

Alternatywa: zostawić trasy mobilne i przepisywać ścieżki w
`redirectSystemPath`. To jednak druga mapa do utrzymania. Wybieramy jedną.

Ekran z linku musi działać „na zimno”: bez sesji, jako pierwszy ekran po
starcie. Jeśli wymaga zalogowania (np. `/orders/...`), zapamiętuje cel i
wraca do niego po logowaniu. Tej logiki nie ma w `+native-intent`, bo nie widzi
on stanu auth.

---

## 6. Projekt URL: jedna domena, jedna ścieżka

**[wniosek]**

- Wszystkie linki z maili kierujemy na **domenę webu** (tę, która serwuje
  Next.js), nie na API (`api.`) ani na `:8081`. Plików AASA i assetlinks nie
  trzeba wtedy wystawiać w Django.
- Bazowy URL frontendu wchodzi jako jedna zmienna środowiskowa, np.
  `FRONTEND_URL`, z której składamy `HEADLESS_FRONTEND_URLS` i `NEWSLETTER_*`.
  Dziś `HEADLESS_FRONTEND_URLS` jest na sztywno na `localhost:8081`. OWASP
  dodatkowo każe składać URL resetu z zaufanej, zakodowanej domeny, a nie z
  nagłówka `Host`
  ([OWASP Forgot Password](https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html)).
  Format `HEADLESS_FRONTEND_URLS` pozwala na dowolny kształt URL z `{key}`
  ([allauth](https://github.com/pennersr/django-allauth/blob/main/docs/headless/configuration.rst)).
- Domena apex (`olivin.pl`) albo `www` — jedna, kanoniczna. AASA i assetlinks
  muszą być na **tej samej** domenie, której używają linki. Przekierowanie
  `olivin.pl → www.olivin.pl` przed plikiem `.well-known` psuje weryfikację
  (TN3155, Android).
- Na webie ekran z linku jest pełnoprawny: użytkownik bez aplikacji kończy
  reset hasła w przeglądarce. Po wydaniu w App Store można dodać Smart App
  Banner, ale to opcja, nie wymóg.

---

## 7. Zawijanie linków przez klientów poczty i ESP

- **Śledzenie kliknięć w ESP** podmienia link na domenę ESP. Twilio SendGrid
  opisuje obejście: link branding na **tej samej** domenie co universal links,
  AASA i assetlinks hostowane na domenie śledzącej, atrybut `universal="true"`
  na linku i ograniczenie AASA do `/uni/*`. Aplikacja musi sama rozwinąć
  zakodowany URL do oryginału i wywołać zdarzenie kliknięcia. Link bez
  atrybutu „will take your recipient to their mobile browser”
  ([SendGrid: Universal Links](https://www.twilio.com/docs/sendgrid/ui/sending-email/universal-links)).
- **Microsoft Defender Safe Links** (Outlook w firmach z Defender for Office 365)
  przepisuje URL na `https://<region>.safelinks.protection.outlook.com/...`
  i skanuje link przy kliknięciu. Wyłączyć to może tylko administrator tenantu
  odbiorcy (lista „Do not rewrite the following URLs”)
  ([Microsoft: Safe Links](https://learn.microsoft.com/en-us/defender-office-365/safe-links-about)).
  Nie mamy na to wpływu.
- Apple: „If the link tapped on by the user is not a universal link but
  redirects to one, the user will be routed through the web browser to the
  app” (TN3155). Po zawinięciu ścieżka jest więc niepewna i zależy od
  przeglądarki.

**[wniosek]**

1. W mailach transakcyjnych (reset, newsletter confirm/unsubscribe, status
   zamówienia) **wyłączamy click tracking** u dostawcy. Mail jest wysyłany przez
   SMTP (`EMAIL_BACKEND = smtp`), a dostawca nie jest zapisany w repo, więc
   to otwarte pytanie.
2. Strona web musi obsłużyć każdy link do końca. Zawinięty link wyląduje w
   przeglądarce i to jest akceptowalny fallback, nie błąd.
3. Skanery (Safe Links, antyspam) mogą otworzyć link przed człowiekiem.
   Pierwszy GET nie może więc zużyć tokenu (sekcja 8).

---

## 8. Bezpieczeństwo tokenu w URL

| Zasada | Źródło | Stan w Olivin |
|---|---|---|
| Token jednorazowy i z terminem ważności | OWASP: „Single use and expire after an appropriate period”, „Invalidated after they have been used” ([OWASP](https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html)) | Reset: generator tokenów Django, domyślnie 3 dni. **[wniosek]** Token przestaje działać po zmianie hasła, bo hash obejmuje hasło. Warto skrócić `PASSWORD_RESET_TIMEOUT` do ~1 h. Newsletter confirm: UUID, sprawdzić, czy po potwierdzeniu jest zerowany. Unsubscribe: celowo wielorazowy, tylko do wypisu |
| GET nie zmienia stanu | allauth `ACCOUNT_CONFIRM_EMAIL_ON_GET` domyślnie `False`: „GET is not designed to modify the server state” ([allauth](https://github.com/pennersr/django-allauth/blob/main/docs/account/configuration.rst)) | Strona z linku pokazuje formularz albo przycisk i dopiero wtedy wysyła POST. Ekrany newslettera nie powinny same wysyłać POST przy otwarciu |
| Klucz nie trafia do URL-a API | Headless API przyjmuje klucz w nagłówku `X-Password-Reset-Key` / `X-Email-Verification-Key` albo w body POST ([allauth OpenAPI](https://github.com/pennersr/django-allauth/blob/main/allauth/headless/spec/doc/openapi.yaml)) | Logi Django/nginx nie widzą klucza w ścieżce API. Widzą go za to logi serwera Next.js przy wejściu na stronę |
| Brak wycieku przez Referer | OWASP: Referrer Policy z wartością `no-referrer` na stronie resetu | Brak. Dodać nagłówek dla `/account/reset-password/*` i `/newsletter/*` w `next.config.ts` (`headers()`) |
| URL budowany z zaufanej domeny | OWASP: nie ufać nagłówkowi `Host` | `HEADLESS_FRONTEND_URLS` jest zakodowane (OK), ale na `localhost` |
| Klucz poza logami | Brak wprost w OWASP | **[wniosek]** Na stronie web: odczyt klucza, potem `history.replaceState` bez klucza. Bez analityki i skryptów firm trzecich na tych trasach. Wyłączyć logowanie query/ścieżki tych tras w proxy, jeśli się da. W aplikacji nie logować `path` z `+native-intent` (Sentry breadcrumbs) |

Unsubscribe konta używa `signing.dumps(pk)`. Komentarz w kodzie wprost zakłada,
że link trafia do logów, dlatego zawiera `pk`, a nie e-mail. Takie podejście
jest spójne z resztą.

---

## 9. Testowanie na Windowsie bez iPhone'a

### Android (pełne pokrycie)

1. Serwer: `curl -v https://<domena>/.well-known/assetlinks.json` (200,
   `application/json`, bez 3xx). Dodatkowo test Google:
   `https://digitalassetlinks.googleapis.com/v1/statements:list?source.web.site=https://<domena>&relation=delegate_permission/common.handle_all_urls`
   ([Digital Asset Links API](https://developers.google.com/digital-asset-links/reference/rest/v1/statements/list)).
2. Domena tymczasowa przed produkcją: `npx expo start --tunnel` z
   `EXPO_TUNNEL_SUBDOMAIN` i ta domena w `intentFilters`
   ([Expo](https://docs.expo.dev/linking/android-app-links/)). **[wniosek]**
   Tunel Expo serwuje bundler Expo, nie Next.js. Do testu z Next.js lepszy jest
   tunel (ngrok/cloudflared) na `:3000` albo środowisko stagingowe.
3. Emulator, build `npx expo run:android` lub EAS dev build, potem:

```sh
adb shell pm set-app-links --package com.olivin.frontend 0 all
adb shell pm verify-app-links --re-verify com.olivin.frontend
adb shell pm get-app-links com.olivin.frontend   # oczekiwane: verified
adb shell am start -a android.intent.action.VIEW -c android.intent.category.BROWSABLE \
  -d "https://<domena>/account/reset-password/test" com.olivin.frontend
```

([Android: verify App Links](https://developer.android.com/training/app-links/verify-android-applinks))

4. Test end-to-end: Gmail na emulatorze, mail z Mailpit/konsoli, klik w link.
   Bez aplikacji (`adb uninstall`) ten sam link otwiera Chrome i stronę Next.js.

### iOS (częściowe pokrycie)

- Serwer można sprawdzić z Windowsa: `curl -v` oraz `curl -A "MyAgent-Bot/*"`
  na AASA (TN3155). **[wniosek]** Stan w CDN Apple podgląda
  `https://app-site-association.cdn-apple.com/a/v1/<domena>`. Adres pochodzi
  z sesji WWDC20 „What's new in universal links”, nie z dokumentacji tekstowej.
- `swcutil` wymaga maca (TN3155). Expo prowadzi test przez instalację na
  urządzeniu ([Expo](https://docs.expo.dev/linking/ios-universal-links/)).
  Associated Domains wymaga płatnego Apple Developer Program, a usługi
  chmurowe z przepodpisaniem (BrowserStack) zwykle psują entitlements. Opcje
  opisuje `docs/research/ios-bez-maca.md`, sekcje 4 i 8.
- Na iPhonie (pożyczonym albo z TestFlight): wkleić link do Notatek, długie
  przytrzymanie → opcja „Otwórz w Olivin”. Settings > Developer > Universal
  Links > Diagnostics (TN3155).
- **[wniosek]** Logikę ekranów (parsowanie `key`, POST, błędy) testuje się
  niezależnie od iOS: trasy expo-router są wspólne, więc Android i web
  (Playwright na Next.js) pokrywają kod. iOS dokłada tylko weryfikację domeny.

---

## 10. Rekomendacja

1. **Ujednolicić ścieżki** (sekcja 5) i przełączyć backend na jedną zmienną
   `FRONTEND_URL` → Next.js. Usunąć martwe klucze z `HEADLESS_FRONTEND_URLS`.
   To jest potrzebne niezależnie od universal links.
2. **Zbudować strony web** dla `/account/reset-password/[key]` i
   `/newsletter/{confirm,unsubscribe}/[token]`. To fallback i jednocześnie
   jedyna ścieżka dla zawiniętych linków. Akcja dopiero po POST,
   `Referrer-Policy: no-referrer`, `replaceState`, bez skryptów firm trzecich.
3. **Android App Links**: Route Handlery `/.well-known/*` w Next.js,
   `intentFilters` z `autoVerify` na jawne prefiksy, test `adb` na emulatorze.
   Da się to zrobić w całości na Windowsie.
4. **iOS universal links**: te same Route Handlery (AASA, tylko format
   `components`) plus `associatedDomains`. Włączyć, gdy jest płatne konto
   Apple i Team ID. Do tego czasu iOS dostaje web, co działa poprawnie.
5. **Click tracking off** dla maili transakcyjnych u dostawcy. Bez
   integracji SendGrid `/uni/*` (YAGNI, dopóki nie mierzymy kliknięć w tych
   mailach).
6. Skrócić `PASSWORD_RESET_TIMEOUT` (np. 3600 s). Rozważyć
   `ACCOUNT_PASSWORD_RESET_BY_CODE_ENABLED = True` dla spójności z weryfikacją
   kodem. Wtedy z allauth znika ostatni link z tokenem, a deep linki zostają
   tylko dla newslettera i zamówień.

Pominięte: biblioteki deferred deep linking (Branch itp.) i strony pośrednie z
wykrywaniem aplikacji. Systemowy fallback do przeglądarki pokrywa przypadek
„brak aplikacji”. Wracamy do tematu, gdy będzie potrzebne „zainstaluj i wróć
do tego samego ekranu”.

---

## 11. Otwarte pytania do właściciela

1. **Domena produkcyjna**: apex czy `www`? Czy web i API będą na osobnych
   hostach (`olivin.pl` + `api.olivin.pl`)?
2. **Reset hasła linkiem czy kodem?** Kod
   (`ACCOUNT_PASSWORD_RESET_BY_CODE_ENABLED`) usuwa problem deep linku dla
   auth w całości, kosztem wpisywania kodu.
3. **Dostawca maili** (SMTP przez kogo?) i czy ma włączone śledzenie
   kliknięć/otwarć. Czy potrzebujemy statystyk kliknięć w mailach
   transakcyjnych?
4. **Które ścieżki ma przejmować aplikacja?** Czy `/cart` i
   `/account/notifications` też, czy tylko auth, newsletter i zamówienia?
5. **Link do zamówienia w mailu o statusie** — dodać? Jeśli tak: wymaga
   logowania czy ma działać przez podpisany token, jak wypis z newslettera?
6. **Apple Developer Program i Team ID**: kiedy? Bez tego iOS dostaje tylko web.
7. **Klucz podpisu Android**: Play App Signing (dwa odciski SHA-256) czy
   własny?
8. **Ekrany newslettera**: potwierdzać automatycznie po otwarciu (wygoda, ryzyko
   skanerów) czy przyciskiem (bezpieczniej)?
