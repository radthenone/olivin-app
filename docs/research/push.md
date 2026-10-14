# Research: powiadomienia push (Expo SDK 57 + Django)

Data: 2026-10-14. Dotyczy decyzji przekrojowej nr 5 z `docs/open-decisions.md`
(„Push: expo-notifications, FCM, APNs i rejestracja urządzeń”).

Stack: Expo SDK 57 (`expo ~57.0.23`), React Native 0.86.3, expo-router, EAS
Build, Android + iOS, Django + Celery. Źródła są pierwotne (dokumentacja Expo,
Firebase, Android, Apple, WebKit, Next.js), a stan repo pochodzi z kodu.
Wnioski własne są oznaczone jako **[wniosek]**.

---

## 1. TL;DR

- **Backend pod Expo Push Service jest w większości gotowy.** Są: model
  `PushDevice`, endpointy rejestracji i wyrejestrowania, adapter
  `ExpoPushProvider` za interfejsem (ADR 0027), zadanie Celery, bramka zgody
  `marketing_push` oraz kasowanie tokenów `DeviceNotRegistered` z ticketów.
- **Mobile nie ma niczego.** Brakuje `expo-notifications`, `projectId` EAS,
  `google-services.json`, kanałów Androida, obsługi tapnięcia i wywołania
  rejestracji i wyrejestrowania.
- **Rekomendacja: zostać przy Expo Push Service.** Direct FCM v1 + APNs daje
  niezależność od Expo kosztem dwóch protokołów i dwóch zestawów sekretów na
  naszym serwerze. Adapter pozwala zmienić dostawcę później bez migracji
  danych.
- **Luki backendu do domknięcia:** sprawdzanie receiptów (Expo wprost tego
  wymaga), retry na 429/5xx, `channelId`/`priority` w wiadomości, pole `url`
  w `data` do deep linku.
- **Web push dla Next.js na teraz nie jest wart zachodu** (uzasadnienie w §10).

---

## 2. Co już istnieje w repo

| Element | Gdzie | Stan |
|---|---|---|
| ADR: push przez adapter, dostawca Expo | `docs/adr/0027-integracje-zewnetrzne-przez-adapter.md` | przyjęty |
| Interfejs `PushProvider.send_push(tokens, title, body, data) -> list[str]` (martwe tokeny) | `backend/src/core/integrations/push/base.py` | gotowy |
| `ExpoPushProvider` (sam `requests`, bez SDK; opcjonalny `EXPO_ACCESS_TOKEN`) | `core/integrations/push/expo.py` | gotowy, tylko tickety |
| `NoopPushProvider` (domyślny), `FakePushProvider` (testy) | `core/integrations/push/noop.py`, `fake.py` | gotowe |
| Wybór dostawcy: `PUSH_PROVIDER`, `EXPO_PUSH_URL`, `EXPO_ACCESS_TOKEN` | `core/settings/base.py:99-108` | gotowe |
| `PushDevice(user FK, token unique, platform ios/android, last_used_at)` | `apps/notifications/models.py` | gotowy |
| `GET/POST /notifications/devices/`, `DELETE /notifications/devices/{token}/` | `apps/notifications/views.py` (`PushDeviceViewSet`) | gotowe |
| Rejestracja idempotentna po tokenie (przejęcie tokenu przez inne konto) | `services.register_push_device` | gotowa |
| `notify()` kolejkuje push po commicie: transakcyjne zawsze, marketing tylko z `marketing_push` | `apps/notifications/services.py` | gotowe |
| `send_push_notification` (Celery): wysyłka na wszystkie urządzenia klienta, kasowanie `DeviceNotRegistered`, odświeżenie `last_used_at` | `apps/notifications/tasks.py` | gotowe |
| Zgoda per kanał: `NotificationPreference.marketing_email` / `marketing_push` | `apps/notifications/models.py` | gotowa (boolean) |
| Zgody wersjonowane: `ConsentDocument` / `Consent` (terms, privacy, marketing) | `apps/consents/models.py` | gotowe, **niepowiązane** z `marketing_push` |
| Mobile: `expo-notifications`, `expo-device` | `frontend/mobile/package.json` | **brak** |
| Mobile: `extra.eas.projectId`, `android.googleServicesFile`, plugin `expo-notifications` | `frontend/mobile/app.config.js` | **brak** |
| Mobile: profil `production` / `preview` w `eas.json` | `frontend/mobile/eas.json` | **brak** (są tylko `development-simulator` i `remote-device`) |
| `android/`, `ios/` | `frontend/mobile/.gitignore` | ignorowane, czyli CNG: config plugin zadziała |
| targetSdk Androida | `node_modules/react-native/gradle/libs.versions.toml` | `36` (≥ 33, więc momentem promptu sterujemy sami) |
| Logout mobile | `src/core/auth/auth.service.ts:213` | kasuje tylko sesję allauth, nie wyrejestrowuje urządzenia |

---

## 3. Porównanie: Expo Push Service a direct FCM v1 + APNs

| Kryterium | Expo Push Service | Direct FCM v1 (Android) + APNs (iOS) |
|---|---|---|
| Token na urządzeniu | `getExpoPushTokenAsync({ projectId })`, czyli `ExponentPushToken[...]` [E1] | `getDevicePushTokenAsync()`, czyli „native FCM, APNs token” [E2] |
| Protokoły po stronie backendu | 1 (JSON over HTTPS do `exp.host`) [E3] | 2: FCM HTTP v1 z OAuth2 z konta serwisowego [F2] oraz APNs HTTP/2 z JWT ES256 z klucza .p8 [A2] |
| Gdzie żyją sekrety FCM/APNs | w EAS (upload klucza FCM V1 i klucza APNs) [E4][E1] | na naszym serwerze (JSON konta serwisowego, .p8, Key ID, Team ID) |
| Biblioteki Python | niepotrzebne, obecny adapter ma ~40 linii; opcjonalnie `exponent_server_sdk` 2.2.0 (ostatnie wydanie 2025-07-03, utrzymywane przez społeczność) [E7] | `firebase-admin` (7.7.0) dla FCM oraz osobny klient HTTP/2 + JWT dla APNs |
| Koszt | „There is no cost associated with sending notifications through Expo push notification service” [E5] | brak opłat za FCM i APNs |
| Limity | 100 wiadomości na żądanie, 600 powiadomień/s na projekt, 1000 ID receiptów na żądanie [E3] | limity FCM i APNs |
| Prywatność treści | Expo trzyma treść „only in memory and in message queues, not in databases”; zespół Expo może ją zobaczyć przy debugowaniu [E5] | treść idzie tylko do Google i Apple |
| Potwierdzenie dostarczenia | ticket, a po ~15 min receipt; receipt `ok` oznacza tylko, że FCM/APNs przyjęły wiadomość [E3] | odpowiedź FCM/APNs od razu |
| Martwy token | `DeviceNotRegistered` w tickecie albo receipcie [E3][E5] | FCM: `UNREGISTERED` (404) / `INVALID_ARGUMENT` (400) przy poprawnym payloadzie [F1]; APNs: odpowiedni kod błędu |
| Uzależnienie | dodatkowy pośrednik (exp.host) | brak pośrednika |
| Zgodność z repo | ADR 0027 i istniejący kod | nowy adapter, ten sam interfejs `PushProvider` |

**[wniosek]** Konta Firebase (FCM V1) i klucza APNs nie da się uniknąć w żadnej
z opcji. Expo nie zwalnia z ich założenia, jedynie trzyma je u siebie. Realny
zysk z Expo to brak dwóch klientów protokołów i brak rotacji JWT na naszym
serwerze (APNs wymaga odświeżania tokenu „at least once an hour” [A2]). Dla
jednego sklepu z niskim wolumenem to przeważa. Do direct można przejść
później: nowy adapter oraz ponowna rejestracja tokenów natywnych (inny format
tokenu, więc stare rekordy `PushDevice` trzeba by wymienić).

---

## 4. Rejestracja urządzenia i cykl życia tokenu

### Przepływ (mobile)

1. Po zalogowaniu, ale **w kontekście** (np. po pierwszym zamówieniu albo
   przy włączeniu „powiadom o dostępności”), a nie na starcie aplikacji
   (zob. §6).
2. `Notifications.setNotificationChannelAsync(...)` dla kanałów Androida.
   Dokumentacja wymaga tego **przed** pobraniem tokenu:
   `setNotificationChannelAsync` musi poprzedzić `getExpoPushTokenAsync` [E2].
3. `getPermissionsAsync`, a jeśli nie przyznano, `requestPermissionsAsync`
   [E1]. Na iOS należy czytać `ios.status`, nie główne `status` [E2].
4. `getExpoPushTokenAsync({ projectId })`. `projectId` pochodzi z
   `Constants.expoConfig.extra.eas.projectId` albo
   `Constants.easConfig.projectId`, a Expo zaleca ustawić go jawnie [E1].
   **W repo go nie ma, trzeba wykonać `eas init`.**
5. `POST /notifications/devices/ {token, platform}`. Endpoint jest już
   idempotentny.
6. `Notifications.addPushTokenListener` przy rotacji tokenu: stary token
   przestaje działać, nowy trzeba wysłać na backend [E2]. Wystarczy ponowny
   POST, bo rejestracja to `update_or_create`.

### Kiedy token się zmienia (Expo FAQ [E5])

- Przy aktualizacji aplikacji **nie** zmienia się („remains the same across
  app upgrades”).
- Android: reinstalacja **może** zmienić token.
- iOS: token „remains the same even after uninstalling the app and
  reinstalling it”.
- Zmienia się przy zmianie `applicationId` lub `experienceId`. Token Expo
  nie wygasa.

### Odinstalowanie

Nie da się go wykryć bezpośrednio. Kolejna wysyłka zwróci
`DeviceNotRegistered`, po czym „you should stop sending notifications to this
token” [E5]. Backend robi to dziś **tylko dla ticketów**, nie dla receiptów
(zob. §8).

### Wylogowanie

- Endpoint `DELETE /notifications/devices/{token}/` istnieje. Token
  `ExponentPushToken[...]` zawiera nawiasy kwadratowe, więc trzeba go
  URL-encodować (`encodeURIComponent`).
- **Kolejność:** najpierw DELETE urządzenia (wymaga sesji), potem
  `deleteAllauthClientV1AuthSession`. Dziś `auth.service.ts` robi tylko to
  drugie.
- **[wniosek]** Jeśli DELETE się nie uda (offline), nic złego się nie
  stanie, bo następny login innego konta na tym urządzeniu przepnie token
  (`update_or_create` po tokenie). Pozostaje okno, w którym poprzedni klient
  dostaje push transakcyjny na urządzenie, z którego się wylogował.
  Akceptowalne; ewentualnie można ponowić DELETE przy następnym starcie.

### Wiele urządzeń na konto

Jest obsłużone: FK `user` oraz `token unique`, a zadanie wysyła na wszystkie
tokeny klienta.

### Nieaktywne tokeny

FCM uznaje rejestrację za nieaktualną po miesiącu bez połączenia, a na
Androidzie po 270 dniach ją usuwa [F1]. Zaleca też codzienne czyszczenie
rekordów starszych niż przyjęte okno [F1]. **[wniosek]** Przy Expo
`DeviceNotRegistered` i tak to wyłapie, więc okresowe czyszczenie po
`last_used_at` (np. powyżej 270 dni) to opcja, nie konieczność.

---

## 5. Konfiguracja poświadczeń

### Android (FCM V1)

1. Projekt Firebase z aplikacją Android `com.olivin.frontend`.
2. `google-services.json` w katalogu projektu mobile oraz
   `expo.android.googleServicesFile` w `app.config.js`. Plik „is required
   for your Android app to be registered with FCM” [E4].
3. Klucz konta serwisowego (Firebase → Settings → Service accounts →
   Generate new private key). Plik należy dodać do `.gitignore` [E4].
4. Upload do EAS: `eas credentials` → Android → production → Google Service
   Account → FCM V1, albo przez expo.dev → Credentials [E4]. Dla
   istniejącego konta serwisowego potrzebna jest rola „Firebase Cloud
   Messaging API Admin” [E4].

**[wniosek]** `google-services.json` zawiera identyfikatory, nie sekrety
serwerowe, więc zwykle trafia do repo. Klucz konta serwisowego **nigdy**.

### iOS (APNs)

- Wymagane płatne konto Apple Developer [E1].
- Przy pierwszym `eas build` dla iOS EAS CLI pyta o włączenie push i
  wygenerowanie klucza APNs; bez builda można użyć `eas credentials` [E1].
- Klucz APNs to plik `.p8` plus 10-znakowy Key ID [A2]. Apple zaleca dziś
  klucze rozdzielone na środowisko (Sandbox i Production). Klucze team-scoped
  działające w obu środowiskach są nadal obsługiwane [A2]. Przy Expo klucz
  trzyma EAS, a nasz backend go nie widzi.

### Backend

- `PUSH_PROVIDER=core.integrations.push.expo.ExpoPushProvider` na produkcji;
  domyślnie jest Noop.
- Zalecane: włączyć „enhanced push security” w EAS i ustawić
  `EXPO_ACCESS_TOKEN`. Bez tego wyciek tokenów urządzeń pozwala każdemu
  „impersonate your server” [E3]. Adapter już wysyła nagłówek `Authorization`.

---

## 6. Uprawnienia: Android 13+ i iOS

### Android 13+ (`POST_NOTIFICATIONS`)

- Na nowej instalacji powiadomienia są **domyślnie wyłączone** [D1].
- Aplikacja targetująca API 33+ (u nas targetSdk 36) „has complete control
  over when the permission dialog is displayed” [D1].
- Prompt systemowy nie pojawi się, dopóki nie istnieje choć jeden kanał [E2].
  Dlatego kanały tworzymy przed `requestPermissionsAsync`.
- Dobre praktyki: pytać w kontekście (akcja użytkownika) i wyjaśnić wartość
  przed promptem [D1].

### iOS

- Prompt pojawia się **tylko raz**: „Subsequent authorization requests
  don't prompt the person” [A1]. Odmowę można cofnąć tylko w Ustawieniach.
- Apple zaleca prośbę w kontekście, a nie przy pierwszym uruchomieniu [A1].
- Alternatywa: **provisional** (`allowProvisional` w expo-notifications
  [E2]). Bez promptu powiadomienia trafiają cicho do Centrum Powiadomień z
  przyciskami Keep / Turn Off [A1].

**[wniosek]** Przyjąć ekran „pre-permission” (nasz własny UI z wyjaśnieniem),
a dopiero po „Tak” wywołać systemowy prompt. To chroni jednorazowy prompt na
iOS. Provisional warto rozważyć dla iOS (zob. pytania otwarte).

---

## 7. Kanały powiadomień (Android)

- Wiadomość z `channelId`, którego nie ma na urządzeniu, **nie zostanie
  wyświetlona**. Bez `channelId` Expo używa kanału „Default” [E3].
- Po utworzeniu kanału można zmienić tylko jego nazwę i opis [E2], więc
  ważność i dźwięk trzeba ustalić od razu.
- Plugin `expo-notifications` ma opcję `defaultChannel` dla FCMv1 oraz
  `icon` (biały PNG 96×96) i `color` [E2].

**Proponowane kanały [wniosek]**, mapowane 1:1 na podział
`TRANSACTIONAL_KINDS` / marketing w backendzie:

| `channelId` | Rodzaje (`NotificationKind`) | Ważność |
|---|---|---|
| `orders` | `order_status_changed`, `order_paid`, `document_ready`, `return_request_status_changed`, `return_settled` | HIGH |
| `marketing` | `watch_restock`, `watch_price_drop`, `cart_reminder` | DEFAULT |

Użytkownik może wtedy wyciszyć marketing w ustawieniach systemu, nie tracąc
statusów zamówień. Backend musi wysyłać `channelId` (dziś tego nie robi), a
interfejs `PushProvider` potrzebuje parametru kategorii lub kanału, np.
wyprowadzanego z `kind` w zadaniu.

---

## 8. Wysyłka, receipty i obsługa błędów

Fakty z dokumentacji Expo [E3]:

- Ticket `ok` oznacza tylko „received by Expo's servers”. Receipt pojawia
  się po przekazaniu do FCM/APNs.
- „We recommend checking push receipts 15 minutes after sending”. Receipty
  są czyszczone po 24 h. „You must check each push receipt”.
- Błędy: `DeviceNotRegistered` (skasować token), `MessageTooBig` (powyżej
  4096 B), `MessageRateExceeded` (backoff), `MismatchSenderId` i
  `InvalidCredentials` (problem konfiguracji, czyli alert dla nas, nie dla
  tokenu), `TOO_MANY_REQUESTS` (ponad 600/s), `PUSH_TOO_MANY_NOTIFICATIONS`
  (ponad 100 wiadomości w żądaniu).
- Ponawiać przy błędach sieci, 429 i 5xx z wykładniczym backoffem; nie
  ponawiać przy 400 [E3].
- Pola: `channelId`, `priority` (Android domyślnie `normal`, który może się
  opóźniać na uśpionym urządzeniu; iOS domyślnie `high`), `ttl` (domyślnie
  4 tygodnie), `sound` (iOS: bez niego cisza), `badge`, `data` (łącznie z
  resztą do ~4 KiB) [E3].

**Luki w obecnym kodzie:**

1. **Brak receiptów.** `ExpoPushProvider` czyta tylko tickety i nie zapisuje
   ID ticketów. Proponowane minimum [wniosek]: zadanie zwraca ID ticketów i
   kolejkuje `check_push_receipts.apply_async(countdown=15*60)` z mapą
   `ticket_id → token`. Przy `DeviceNotRegistered` kasuje token, przy
   `InvalidCredentials` i `MismatchSenderId` loguje na poziomie ERROR. Bez
   nowego modelu, bo mapa jedzie w argumentach zadania.
2. **Brak retry.** `send_push_notification` połyka `PushProviderError`.
   Wystarczy `autoretry_for=(PushProviderError,)`, `retry_backoff=True`,
   `max_retries` około 5, ale tylko dla błędów przejściowych (adapter
   musiałby odróżnić 4xx od 5xx/429).
3. **Brak `channelId`, `priority`, `sound`.** Bez `sound: "default"` iOS
   dostarcza po cichu [E3]. Dla transakcyjnych: `priority: "high"`, kanał
   `orders`.
4. **Brak `url` w `data`.** `data` to dziś surowy payload (np.
   `order_number`). Do deep linku potrzebne jest `data.url` (zob. §9).
5. **Batch powyżej 100 tokenów.** Zadanie działa per klient, więc w praktyce
   nie przekroczy 100. **[wniosek]** Bez chunkowania, dopóki nie pojawi się
   masowa wysyłka jednym żądaniem.

Wiadomości `MessageTooBig` zapobiega już `push_body` (krótsza treść) dla
`cart_reminder`.

---

## 9. Deep link po tapnięciu (expo-router)

Dokumentacja expo-notifications ma gotowy wzorzec dla Expo Router [E2].
Hook `useNotificationObserver` w root layoutcie:

- na starcie sprawdza `Notifications.getLastNotificationResponse()`
  (aplikacja uruchomiona z powiadomienia),
- subskrybuje `addNotificationResponseReceivedListener` (tapnięcia podczas
  działania),
- gdy `data.url` jest stringiem, wywołuje `router.push(url)`.

Do tego `Notifications.setNotificationHandler(...)` decyduje, czy pokazywać
powiadomienie, gdy aplikacja jest na pierwszym planie. Bez handlera domyślnie
**nie pokazuje** [E2].

**[wniosek] Integracja z repo:**

- Hook trafia do `app/_layout.tsx` (`RootNavigator`), **po** rozstrzygnięciu
  auth, bo trasy `(app)/` są chronione.
- Backend ustawia `data.url` jako ścieżkę wewnętrzną, np.
  `/orders/{number}`. Najlepiej w `notify()` przez `push_data` albo
  mapowanie `kind → ścieżka` w jednym miejscu backendu.
- Repo ma już `app/+native-intent.tsx`. Ścieżki z powiadomień nie
  przechodzą przez system linków, więc ten plik ich nie dotyczy, ale
  schemat ścieżek warto uzgodnić z decyzją nr 6 (deep linki z maili), żeby
  mail i push wskazywały te same trasy.

---

## 10. Testowanie bez fizycznego iPhone'a

- **Expo Go nie obsługuje zdalnych pushy na Androidzie od SDK 53.** „A
  development build is required” [E2]. Profil `development-simulator`
  (`developmentClient: true`) już jest w `eas.json`.
- **Android:** wystarczy emulator z Google Play services [E1]. Pełny tor
  (token, backend, Expo, FCM, tapnięcie) da się przetestować na Windowsie.
- **iOS Simulator:** zdalne pushe działają od Xcode 14 tylko „in macOS 13
  on Mac computers with Apple silicon or T2 processors”, przez APNs Sandbox
  [A3]. **[wniosek]** Z Windowsa się nie da. Potrzebny jest Mac (własny lub
  wynajęty w chmurze) albo fizyczny iPhone zarejestrowany w EAS (Expo każe
  zarejestrować urządzenie przed pierwszym `eas build` [E1]). Zbieżne z
  decyzją nr 8 w `open-decisions.md`.
- **Narzędzia wysyłki:** narzędzie push na expo.dev (wysyłka na token z
  dev builda) [E1] oraz Apple Push Notification Console (wysyłka testowa na
  token APNs, log dostarczeń w środowisku development) [A4].
- **Backend:** `FakePushProvider` już jest. Testy receiptów i retry
  należałoby dopisać do niego (np. `fail_with`, kody receiptów).

---

## 11. Zgoda per kanał

Stan obecny:

- `NotificationPreference.marketing_push` (boolean, domyślnie `False`)
  bramkuje marketing push. Transakcyjne idą zawsze, a gość nigdy nie dostaje
  pusha (`_should_send_push`).
- Osobno istnieje wersjonowana zgoda `Consent(document.kind="marketing")`
  zbierana przy rejestracji (`core/services/allauth/signup_consents.py`).
  **Kod nie wiąże jej z `marketing_push` ani `marketing_email`.**
- Uprawnienie systemowe (OS) to trzecia, niezależna warstwa: klient może
  mieć `marketing_push=True` i wyłączone powiadomienia w systemie, albo
  odwrotnie.

**[wniosek]**

- Uprawnienie OS **nie jest** zgodą marketingową i nie powinno ustawiać
  `marketing_push`. Dobrze, że to osobne pola.
- Ekran zgód w aplikacji powinien pokazywać `marketing_push` obok stanu
  uprawnienia OS, z linkiem do ustawień systemu, gdy OS blokuje.
- `marketing_push` nie ma wersji dokumentu ani znacznika czasu udzielenia
  (poza `updated_at`). Czy to wystarcza jako dowód zgody na marketing push,
  to pytanie prawne (zob. pytania otwarte). Research nie rozstrzyga
  przepisów.

---

## 12. Web push dla Next.js: czy warto?

Fakty:

- Next.js ma oficjalny przewodnik: VAPID, `web-push`, service worker,
  manifest [N1].
- iOS/iPadOS obsługuje web push od 16.4, ale **tylko dla web app dodanej do
  ekranu głównego**, a prośba o zgodę musi wynikać z akcji użytkownika [W1].
- Expo Push Service i `getExpoPushTokenAsync` dotyczą Android i iOS.
  `getDevicePushTokenAsync` ma w dokumentacji „Supported platforms: Android,
  iOS” [E2]. Web push to **trzeci, osobny kanał**: inny model subskrypcji
  (endpoint + klucze), inny adapter (np. `pywebpush` po stronie Django),
  własna obsługa wygasłych subskrypcji.

**[wniosek] Nie teraz.**

- Web ma już e-mail i listę `Notification` w aplikacji, a transakcyjne
  komunikaty i tak idą e-mailem.
- Na iPhone'ach web push wymaga instalacji PWA, czego klient sklepu
  zwykle nie robi.
- Koszt to nowy model, endpointy, service worker, VAPID i UI zgód.
- Wrócić do tematu, gdy będą dane o użytkownikach webowych obserwujących
  warianty (`watch_restock`), dla których mail jest za wolny.

---

## 13. Rekomendacja

1. **Zostać przy Expo Push Service** (zgodnie z ADR 0027). Nie dodawać
   `exponent_server_sdk`, bo obecny adapter na `requests` jest mniejszy od
   tej zależności.
2. **Backend** (jeden ticket):
   - receipty po 15 min z kasowaniem `DeviceNotRegistered`,
   - retry z backoffem na 429/5xx,
   - `channelId` + `priority` + `sound` wyprowadzane z `kind`,
   - `data.url` do deep linku,
   - na produkcji: `PUSH_PROVIDER=…ExpoPushProvider` + `EXPO_ACCESS_TOKEN`
     (enhanced security).
3. **Mobile** (jeden lub dwa tickety):
   - `npx expo install expo-notifications expo-device` i plugin z
     `defaultChannel`, `icon`, `color`,
   - `eas init` (dla `projectId`), `google-services.json`, klucz FCM V1 w
     EAS, klucz APNs przy pierwszym buildzie iOS,
   - kanały `orders` i `marketing`, pre-permission UI, potem prompt
     systemowy,
   - rejestracja po loginie, `addPushTokenListener`, DELETE przed logoutem,
   - `useNotificationObserver` w root layoutcie.
4. **Web push:** odłożyć.
5. **Test:** pełny tor na emulatorze Androida. iOS po zdobyciu
   iPhone'a lub Maca (decyzja nr 8).

---

## 14. Pytania otwarte do właściciela

1. **Zgoda prawna na marketing push.** Czy boolean `marketing_push` bez
   wersji dokumentu wystarcza, czy marketing push ma iść przez wersjonowany
   `Consent` (jak `marketing` przy rejestracji)? Czy zgoda `marketing` z
   rejestracji ma automatycznie włączać `marketing_push` i
   `marketing_email`? Wymaga opinii prawnej (przepisy o marketingu
   bezpośrednim na urządzeniach końcowych); ten research ich nie weryfikuje.
2. **Czy `watch_restock` i `watch_price_drop` są marketingiem?** Klient sam
   włączył obserwację, więc można argumentować, że to usługa na żądanie, a
   nie marketing. Dziś są marketingiem i bez `marketing_push` nie dojdą.
3. **Moment prośby o uprawnienie.** Po pierwszym zamówieniu, przy
   włączeniu obserwacji, czy na ekranie ustawień? Czy na iOS użyć
   provisional?
4. **iOS:** kto i kiedy zakłada płatne konto Apple Developer i skąd
   iPhone lub Mac do testów (łączy się z decyzją nr 8)?
5. **Firebase:** czy jest już projekt (np. dla Google Sign-In)? Jeśli tak,
   podpiąć do niego FCM; jeśli nie, założyć nowy.
6. **Wylogowanie offline:** czy akceptujemy okno, w którym wylogowany
   klient dostaje push transakcyjny do czasu następnego logowania na tym
   urządzeniu?
7. **Prywatność:** czy treść powiadomień (numer zamówienia, kwota zwrotu)
   może przechodzić przez Expo, które trzyma ją w pamięci i kolejkach, a
   zespół Expo może ją zobaczyć przy debugowaniu [E5]? Jeśli nie, to argument
   za direct FCM/APNs albo za ograniczeniem treści pusha do „Zmiana statusu
   zamówienia” bez szczegółów.

---

## Źródła

- [E1] Expo, *Push notifications setup*:
  https://docs.expo.dev/push-notifications/push-notifications-setup/
- [E2] Expo SDK, *Notifications* (expo-notifications API, config plugin,
  Android 13, Expo Go, Expo Router):
  https://docs.expo.dev/versions/latest/sdk/notifications/
- [E3] Expo, *Send notifications with the Expo Push Service* (endpointy,
  limity, tickety i receipty, błędy, pola, access token):
  https://docs.expo.dev/push-notifications/sending-notifications/
- [E4] Expo, *Add Android FCM V1 credentials*:
  https://docs.expo.dev/push-notifications/fcm-credentials/
- [E5] Expo, *Push notifications: FAQ* (koszt, prywatność, zmiany tokenu,
  odinstalowanie, tokeny natywne):
  https://docs.expo.dev/push-notifications/faq/
- [E7] expo-community, *expo-server-sdk-python*:
  https://github.com/expo-community/expo-server-sdk-python ; PyPI
  `exponent_server_sdk` 2.2.0 (2025-07-03):
  https://pypi.org/project/exponent_server_sdk/
- [F1] Firebase, *Best practices for FCM registration token management*:
  https://firebase.google.com/docs/cloud-messaging/manage-tokens
- [F2] Firebase, *Send a message using FCM HTTP v1 API*:
  https://firebase.google.com/docs/cloud-messaging/send/v1-api
- [D1] Android Developers, *Notification runtime permission*:
  https://developer.android.com/develop/ui/views/notifications/notification-permission
- [A1] Apple, *Asking permission to use notifications*:
  https://developer.apple.com/documentation/usernotifications/asking-permission-to-use-notifications
- [A2] Apple, *Establishing a token-based connection to APNs*:
  https://developer.apple.com/documentation/usernotifications/establishing-a-token-based-connection-to-apns
- [A3] Apple, *Xcode 14 Release Notes* (remote notifications w Simulatorze):
  https://developer.apple.com/documentation/xcode-release-notes/xcode-14-release-notes
- [A4] Apple, *Testing notifications using the Push Notification Console*:
  https://developer.apple.com/documentation/usernotifications/testing-notifications-using-the-push-notification-console
- [W1] WebKit, *Web Push for Web Apps on iOS and iPadOS*:
  https://webkit.org/blog/13878/web-push-for-web-apps-on-ios-and-ipados/
- [N1] Next.js, *Progressive Web Apps* (sekcja Web Push):
  https://nextjs.org/docs/app/guides/progressive-web-apps
