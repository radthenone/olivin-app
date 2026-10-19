# iOS bez maca i bez iPhone'a — jak budować, uruchamiać i testować Olivin

Stan na 2026-10-14. Kontekst: Windows 11, brak maca i iPhone'a. Aplikacja to Expo SDK 57,
React Native 0.86, expo-router, EAS (`frontend/mobile`). Powiązane: #94 (narzędzia do urządzeń),
`frontend/mobile/README.md`, `frontend/mobile/eas.json`, ADR 0020 (Maestro).

Źródła to dokumentacja Expo, Apple, AWS, Maestro i Appetize oraz ich cenniki. Ceny pochodzą
z tych stron w dniu badania i mogą się zmienić. Tam, gdzie źródło pierwotne czegoś nie mówi,
jest to zaznaczone.

## TL;DR

- **Build iOS na symulator** z Windowsa działa już dziś przez EAS Build, bez konta Apple Developer
  i bez maca. Profile `remote-device` / `development-simulator` w `eas.json` są na to gotowe.
- **Uruchomienie** takiego builda bez maca daje chmurowy symulator: EAS Simulator (waitlista,
  brak cennika) albo Appetize.io (od ręki, 30 min/mies. za darmo).
- **E2E na iOS** da się uruchomić bez maca: Maestro w EAS Workflows (job `maestro` na buildzie
  symulatorowym) albo Maestro Cloud ($250/urządzenie/mies.).
- **Fizyczne urządzenie** (TestFlight, ad hoc, push z APNs na produkcji, Universal Links,
  Apple Pay) wymaga **Apple Developer Program za $99/rok**, a TestFlight i build ad hoc wymagają
  **prawdziwego iPhone'a**. Zamiast własnego są chmurowe farmy urządzeń (BrowserStack, AWS
  Device Farm), ale też potrzebują .ipa podpisanego płatnym kontem.
- **Minimalny koszt do etapu „aplikacja wstaje i przechodzi E2E na iOS”: $0–19/mies.** Koszt
  do wydania w App Store: + $99/rok i dostęp do jakiegokolwiek iPhone'a na testy końcowe.

## 1. EAS Build: build iOS z Windowsa

### Build na symulator (`ios.simulator: true`)

- Build na symulator daje samodzielną wersję aplikacji „bez wdrażania do TestFlight ani nawet
  posiadania konta Apple Developer”
  ([Expo: Build for iOS Simulators](https://docs.expo.dev/build-reference/simulators/)).
- Wynikiem jest `.app` (nie `.ipa`), więc nie da się go zainstalować na iPhonie, tylko na
  symulatorze. Właśnie tego formatu oczekują Appetize, EAS Simulator i Maestro (niżej).
- Build odbywa się na macOS w chmurze EAS, więc Windows nie ma znaczenia.
- `frontend/mobile/eas.json` ma już dwa takie profile: `remote-device` (instalowalny build,
  `ios.simulator: true`) i `development-simulator` (to samo z `developmentClient: true`, czyli
  hot reload przez Metro). Taski: `task mobile:eas:build:simulator -- ios`.

### Build na urządzenie (`.ipa`)

- Dystrybucja wewnętrzna (ad hoc) na iOS „wymaga płatnego konta Apple Developer”; urządzenie
  rejestruje się przez `eas device:create`, a limit to 100 iPhone'ów rocznie
  ([Expo: Internal distribution](https://docs.expo.dev/build/internal-distribution/)).
- Rejestracja urządzenia polega na otwarciu wygenerowanego linku **na samym iPhonie**
  i zainstalowaniu profilu. Od iOS 16 trzeba też włączyć Developer Mode. Apple może przetwarzać
  nowe urządzenie 24–72 godziny
  ([Expo: iOS development build for devices](https://docs.expo.dev/tutorial/eas/ios-development-build-for-devices/)).
  Bez fizycznego iPhone'a ta ścieżka odpada.
- Certyfikaty i profile EAS generuje i trzyma po swojej stronie, więc mac nie jest potrzebny
  także tutaj.

### Koszt EAS Build ([expo.dev/pricing](https://expo.dev/pricing))

| Plan       | Cena/mies.                  | Buildy                         |
| ---------- | --------------------------- | ------------------------------ |
| Free       | $0                          | do 15 buildów iOS + 15 Android |
| Starter    | $19 + zużycie               | $45 kredytu                    |
| Production | $199 + zużycie              | $225 kredytu                   |
| Enterprise | od $1000                    | wg umowy                       |

- Build iOS ponad kredyt: $2 (medium) albo $4 (large) za sztukę.
- Na Free buildy mają niski priorytet i w szczycie czekają ponad 90 min. Limit czasu buildu to
  45 min (na płatnych 2 h). Limity planu Free odnawiają się co miesiąc
  ([Expo: Plans](https://docs.expo.dev/billing/plans/)).

## 2. Apple Developer Program

- Kosztuje **$99 rocznie**. Enterprise kosztuje $299 rocznie i służy tylko do dystrybucji
  wewnątrz organizacji ([Apple Developer Program](https://developer.apple.com/programs/)).
- Darmowe konto (Apple Account + Apple Developer Agreement) **nie pozwala dystrybuować**
  aplikacji. Nie ma w nim TestFlight ani App Store. Profile wygasają po 7 dniach, a limity to
  3 urządzenia i 10 App ID ([Apple: Compare memberships](https://developer.apple.com/support/compare-memberships/)).
  Darmowe podpisywanie działa i tak tylko przez Xcode, czyli na macu.
- Do czego potrzebny jest płatny Program w naszym przypadku:
  - build `.ipa` na urządzenie (ad hoc lub development) — [Expo](https://docs.expo.dev/build/internal-distribution/);
  - TestFlight i App Store — [Apple](https://developer.apple.com/programs/);
  - poświadczenia push (APNs): „A paid Apple Developer Account is required to generate
    credentials” ([Expo: Push setup](https://docs.expo.dev/push-notifications/push-notifications-setup/));
  - `eas submit` — działa na Windowsie, ale wymaga płatnego konta. W trybie nieinteraktywnym
    (CI) potrzebny jest App Store Connect API key ([Expo: Submit to App Store](https://docs.expo.dev/submit/ios/)).
- Strona Apple z listą funkcji (Push, Apple Pay, Associated Domains, Sign in with Apple)
  w podziale na typ konta ([Supported capabilities](https://developer.apple.com/help/account/reference/supported-capabilities-ios))
  nie dała się odczytać maszynowo, bo checkmarki w tabeli znikają. W praktyce wszystkie te
  funkcje wymagają płatnego Programu, ale nie potwierdziłem tego w źródle.

## 3. Chmurowe symulatory iOS

### EAS Simulator (Expo)

- To **ograniczony podgląd (limited-access preview)**: „nie jest objęty planami płatnymi ani
  darmowymi” i jest dostępny „tylko dla wybranych partnerów”. Dostęp daje waitlista
  ([Expo docs: EAS Simulator](https://docs.expo.dev/preview/eas-simulator/introduction),
  [expo.dev/services/simulators](https://expo.dev/services/simulators)). Komendy `simulator:*`
  są eksperymentalne.
- Działa z iOS Simulator i Android Emulator, ale nie z fizycznymi urządzeniami. Expo wprost
  pisze, że daje użytkownikom Windowsa i Linuksa symulator iOS.
- Źródłem aplikacji może być EAS Build (`--build-id`), fingerprint, URL do archiwum albo
  Expo Go.
- Sesja trwa maksymalnie **40 min na Free i 115 min na planach płatnych**. Bez
  `--max-idle-time-minutes` nie ma limitu bezczynności. Sesje czekają w tej samej puli
  współbieżności co EAS Build ([CLI reference](https://docs.expo.dev/preview/eas-simulator/reference/cli.md),
  [Troubleshooting](https://docs.expo.dev/preview/eas-simulator/troubleshooting.md)).
  README podaje „max 30 min / 10 min bezczynności”. To prawdopodobnie wartości z taska
  (`taskfiles/mobile.yml`), a nie limit usługi; warto to doprecyzować.
- **Cennika nie ma.** Dokumentacja mówi tylko, że sesja bez nadzoru „zużywa usage”, dopóki się
  nie zatrzyma. Na stronie z cenami nic o tym nie ma.
- Do pętli dev: build `development-simulator` + `EXPO_UNSTABLE_TUNNEL_V2=1 expo start --tunnel`
  + `simulator:start --open-url …`, a zmiany są widoczne przez Fast Refresh
  ([blog Expo, 2026-09-14](https://expo.dev/blog/build-ios-apps-on-windows-with-cloud-simulators)).
  Kamera jest symulowana (wzór testowy albo wgrane zdjęcie lub wideo).
- Na Androidzie EAS Simulator jest „nadal w budowie”, a podgląd w przeglądarce może nie
  reagować na input ([Troubleshooting](https://docs.expo.dev/preview/eas-simulator/troubleshooting.md)).

### Appetize.io: dostępny od ręki

- Przyjmuje `.zip` / `.tar.gz` ze spakowanym `.app` z **builda na symulator**. Buildów
  urządzeniowych (`.ipa`) nie obsługuje ([Appetize: iOS uploads](https://docs.appetize.io/platform/app-management/uploading-apps/ios)).
  Nasz build z profilu `remote-device` pasuje bez zmian.
- Ceny ([appetize.io/pricing](https://appetize.io/pricing)):

  | Plan    | Cena           | Minuty                               | Aktywne urządzenia |
  | ------- | -------------- | ------------------------------------ | ------------------ |
  | Free    | $0             | 30 min/mies.                         | 2                  |
  | Starter | $59/mies.      | 500 min, potem $0,06/min             | 3                  |
  | Premium | $319/mies.     | 500 min, potem $0,06/min             | 16                 |

- To build release, bez hot reloadu. Nadaje się do odpowiedzi na pytanie „czy wstaje i jak
  wygląda”, a nie do pętli dev.

## 4. Prawdziwe urządzenia w chmurze

### BrowserStack App Live / App Automate

- Wymaga `.ipa` wyeksportowanego jako **Ad Hoc, Enterprise albo Development, nie App Store**.
  BrowserStack przepodpisuje aplikację własnym profilem. Entitlements (np. push, associated
  domains) testuje tylko dla aplikacji podpisanych certyfikatem **Enterprise**
  ([BrowserStack: .ipa creation](https://www.browserstack.com/docs/app-automate/appium/references/ipa-creation),
  [iOS entitlements w App Live](https://www.browserstack.com/docs/app-live/advanced-features/iOS-entitlements),
  [FAQ instalacji .ipa](https://www.browserstack.com/support/faq/app-live/features-app-live/why-does-my-ipa-file-ios-app-fail-to-install)).
- Do takiego .ipa potrzebny jest płatny Apple Developer Program.
- Cennika App Live nie udało się odczytać ze strony. Plan „Live” Desktop & Mobile kosztuje
  $39/mies. przy rozliczeniu rocznym, ale dotyczy przeglądarek, nie aplikacji
  ([BrowserStack pricing](https://www.browserstack.com/pricing?product=app-live)). Cenę
  trzeba sprawdzić ręcznie.
- Przepodpisanie oznacza, że push z APNs i Universal Links na tych urządzeniach zwykle nie
  zadziałają tak jak na urządzeniu z naszym profilem. To wniosek z opisu entitlements, nie
  wprost ze źródła.

### AWS Device Farm

- Kosztuje **$0,17 za minutę urządzenia**. Jednorazowy trial to 1000 min (oferta czasowa,
  standardowo 250 min). Wariant „unlimited” kosztuje od $250/mies. za slot, a prywatne
  urządzenia od $200/mies. ([AWS Device Farm pricing](https://aws.amazon.com/device-farm/pricing/)).
- Strona o typach testów iOS nie dała się odczytać. Zgodnie z praktyką Device Farm wymaga
  `.ipa` podpisanego na urządzenie (dev lub ad hoc), więc znów potrzebny jest płatny Program.
  **Niezweryfikowane w źródle.**

## 5. E2E: Maestro na iOS bez maca (ADR 0020)

Lokalny Maestro dla iOS potrzebuje symulatora, czyli maca. Bez maca są dwie drogi.

### Job `maestro` w EAS Workflows

- Workflow ma job `type: build` (profil z `ios.simulator: true`, buduje `.app`) i job
  `type: maestro` z `build_id` i `flow_path`
  ([Expo: E2E tests w Workflows](https://docs.expo.dev/eas/workflows/examples/e2e-tests/),
  [Pre-packaged jobs](https://docs.expo.dev/eas/workflows/pre-packaged-jobs/)).
  Expo opisuje joby Maestro jako „in alpha”. Przykładowy profil ma
  `"withoutCredentials": true`, więc konto Apple nie jest potrzebne.
- Koszt ([expo.dev/pricing](https://expo.dev/pricing)): **$0,05 za job Maestro + minuty CI**
  (macOS medium $0,075/min, large $0,150/min). **Plan Free nie obejmuje jobów Maestro**, więc
  potrzebny jest co najmniej Starter ($19/mies.). Free daje do 60 min CI/CD i 1 równoległy
  job na macOS.
- Szacunek: 10 min na macOS medium to $0,75 + $0,05 ≈ **$0,80 za przebieg**, nie licząc buildu
  ($2 za build iOS medium ponad kredyt). Przy smoke'u E2E na każdym PR-ze kredyt $45 ze
  Startera starczy na kilkadziesiąt przebiegów miesięcznie. To mój szacunek, nie cena ze źródła.

### Maestro Cloud

- Kosztuje **$250 za urządzenie miesięcznie** (rozliczane za maks. liczbę równoległych
  wykonań). Jest trial. Obejmuje hostowane urządzenia Android, iOS i web
  ([maestro.dev/pricing](https://maestro.dev/pricing)).
- Dla iOS przyjmuje `.app` z **builda na symulator**
  (`maestro cloud --app-file … --flows …`). Dokumentacja nie wspomina o prawdziwych
  iPhone'ach ([Maestro: Run tests in the cloud](https://docs.maestro.dev/cloud/run-maestro-tests-in-the-cloud)).
- W EAS Workflows jest też osobny job `maestro-cloud`, który wymaga konta i planu Maestro Cloud.

Wniosek: dla nas job `maestro` w EAS jest ok. 10× tańszy od Maestro Cloud i używa tego samego
builda.

## 6. TestFlight

- Testerzy instalują aplikację TestFlight **na swoich urządzeniach**
  ([Apple: TestFlight overview](https://developer.apple.com/help/app-store-connect/test-a-beta-version/testflight-overview)).
  Build działa 90 dni. Testerów wewnętrznych może być do 100, zewnętrznych do 10 000. Pierwszy
  build dla testerów zewnętrznych przechodzi review.
- Wymaga płatnego Programu. Wysyłka działa z Windowsa przez `eas build --profile production`
  + `eas submit` ([Expo: Submit](https://docs.expo.dev/submit/ios/)).
- **Bez żadnego iPhone'a TestFlight nic nie daje** — nie ma gdzie go uruchomić. Wystarczy
  jednak telefon testera (znajomy, klient, beta-tester), więc własny iPhone nie jest
  konieczny. Rejestracja UDID też nie jest potrzebna, w przeciwieństwie do ad hoc.

## 7. Wynajem maca w chmurze

### AWS EC2 Mac

- Działa na dedykowanym hoście z rozliczaniem co sekundę, ale z **minimum 24 godzin**
  (wymóg licencji Apple). Dostępne są M1 (`mac2.metal`), M2 (`mac2-m2.metal`) i M4
  (`mac-m4.metal`) ([AWS: EC2 Mac](https://aws.amazon.com/ec2/instance-types/mac/),
  [Dedicated Hosts pricing](https://aws.amazon.com/ec2/dedicated-hosts/pricing/)).
- Stawek godzinowych strony AWS nie podają wprost, trzeba je sprawdzić w AWS Pricing
  Calculator. Wiadomo tylko, że minimalny jednorazowy koszt to 24 h × stawka hosta, a stawka
  wynosi kilka dolarów za godzinę.

### MacinCloud

- Oficjalna strona z cenami zwróciła 404. Źródła wtórne podają ok. $1/h w pay-as-you-go
  i ok. $25–29/mies. za plany „managed” z dziennym limitem godzin
  ([Green Mini, czerwiec 2026 — konkurent, może nie być neutralny](https://www.greenmini.nl/compare/macincloud-alternative/)).
  **Niezweryfikowane w źródle pierwotnym.**

### Kiedy wynajem ma sens

- Wynajęty mac daje Xcode i lokalny Simulator: `expo run:ios`, debugowanie natywne,
  Instruments, lokalny Maestro i `expo-device-hub` dla iOS.
- Nie daje fizycznego iPhone'a, więc push, Universal Links i Apple Pay nadal nie są
  przetestowane na urządzeniu.
- Przy aplikacji Expo bez własnego kodu natywnego EAS Build + chmurowy symulator pokrywa to
  samo taniej. Wynajem ma sens dopiero przy debugowaniu crasha natywnego, którego nie widać
  w logach EAS.

## 8. Co wymaga prawdziwego urządzenia (albo przynajmniej płatnego konta)

| Funkcja                       | Symulator (w tym chmurowy)                                                                                                                                                                                                                                                           | Uwagi                                                                                                                                                      |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Push (APNs)                   | Od Xcode 14: Simulator z iOS 16 na macOS 13 (Apple silicon/T2) odbiera prawdziwe pushe z **APNs Sandbox**; tokeny mogą być dłuższe niż na urządzeniu ([Xcode 14 release notes](https://developer.apple.com/go/?id=xcode-14-sdk-rn)). Expo dopuszcza test w symulatorze ([Expo](https://docs.expo.dev/push-notifications/push-notifications-setup/)). | Poświadczenia APNs wymagają płatnego konta. Produkcyjny APNs i zachowanie w tle trzeba sprawdzić na urządzeniu. Czy EAS Simulator przepuszcza APNs — **nieopisane**. |
| Universal Links               | Dokumentacja Expo prowadzi przez instalację na urządzeniu („Install the app on your iOS device to trigger the verification process”) ([Expo: iOS Universal Links](https://docs.expo.dev/linking/ios-universal-links/)).                                                                | Wymaga Associated Domains (App ID w Apple Developer Console), czyli płatnego konta. Customowe schemy (`olivin://`) działają na symulatorze.                  |
| Apple Pay                     | Testy w sandboksie wymagają obsługiwanego iPhone'a, iPada lub Apple Watcha, konta sandbox testera i karty testowej w Wallet ([Apple Pay sandbox](https://developer.apple.com/apple-pay/sandbox-testing/)).                                                                                | Płatne konto (merchant ID).                                                                                                                                |
| Kamera                        | W EAS Simulator jest symulowana ([blog Expo](https://expo.dev/blog/build-ios-apps-on-windows-with-cloud-simulators)).                                                                                                                                                                  | Prawdziwy obraz i wydajność tylko na urządzeniu.                                                                                                           |
| Wydajność, pamięć, bateria    | Symulator działa na sprzęcie maca.                                                                                                                                                                                                                                                   | Tylko urządzenie.                                                                                                                                          |
| Face ID, NFC, Bluetooth, sensory | Częściowo symulowane albo niedostępne.                                                                                                                                                                                                                                         | Wiedza ogólna; strona Apple o Simulator nie dała się odczytać.                                                                                             |

Olivin dziś (wg `app.config.js`) **nie używa** push, Apple Pay ani Universal Links. Ma customowe
schemy i logowanie Google/Facebook przez `expo-web-browser`, które działa na symulatorze.
Tabela dotyczy więc przyszłych funkcji, nie obecnego stanu.

## 9. Rekomendacja: minimalna ścieżka

**Etap A — „czy iOS wstaje” ($0, od zaraz)**

1. `bunx eas-cli init`, potem `task mobile:eas:build:simulator -- ios` (plan Free, bez konta
   Apple).
2. Spakować `.app` i wgrać do **Appetize Free** (30 min/mies.). To ręczny smoke wyglądu
   i nawigacji na iOS.
3. Równolegle czekać na **EAS Simulator** z waitlisty (#94). Gdy przyjdzie dostęp, zastępuje
   Appetize i daje pętlę dev z Fast Refresh przez tunel.

**Etap B — E2E na iOS w CI (~$19/mies. + ok. $1–3 za przebieg)**

4. Plan Expo **Starter** + EAS Workflow: `build` (profil symulatorowy) → `maestro` z flow'ami
   z ADR 0020. Odpalać na merge do `dev` albo nightly, nie na każdym PR-ze, żeby nie przepalać
   kredytu.

**Etap C — przed pierwszym wydaniem (+ $99/rok)**

5. **Apple Developer Program**, potem `eas build --profile production` + `eas submit`
   z Windowsa i **TestFlight** u co najmniej jednej osoby z iPhone'em.
6. Push, Universal Links i Apple Pay (jeśli wejdą) testować przez TestFlight na tym iPhonie.
   AWS Device Farm ($0,17/min) tylko doraźnie, gdy potrzebny jest konkretny model lub wersja iOS.

**Nie polecam**: Maestro Cloud ($250/urządzenie/mies., to samo co job `maestro` w EAS), stałego
wynajmu maca (EC2 Mac ma minimum 24 h; MacinCloud tylko doraźnie przy natywnym crashu) ani
BrowserStacka jako podstawowej ścieżki (przepodpisanie psuje entitlements).

| Etap       | Koszt                                      |
| ---------- | ------------------------------------------ |
| A          | $0                                         |
| B          | $19/mies. + zużycie ponad $45 kredytu      |
| C          | + $99/rok (+ ewentualnie Device Farm doraźnie) |

## 10. Otwarte pytania do właściciela

1. **Logowanie a App Store 4.8**: aplikacja ma logowanie Google i Facebook. Wytyczna 4.8
   wymaga wtedy równoważnej opcji logowania, która ogranicza dane do imienia i e-maila oraz
   pozwala ukryć e-mail (w praktyce **Sign in with Apple**), chyba że zachodzi któryś wyjątek
   ([App Review Guidelines 4.8](https://developer.apple.com/app-store/review/guidelines/#login-services)).
   Czy to w planie przed wydaniem na iOS? Sign in with Apple wymaga płatnego konta.
2. **Kiedy płatny Apple Developer Program?** Etapy A i B go nie potrzebują. Zakup i weryfikacja
   konta (zwłaszcza jako organizacja — D-U-N-S) to kilka dni, a urządzenia mogą czekać 24–72 h.
3. **Czy jest jakiś iPhone w zasięgu** (rodzina, znajomy, tester), żeby TestFlight miał sens?
   A może kupić tani używany iPhone z iOS w wersji wspieranej przez SDK 57?
4. **Status waitlisty EAS Simulator** i jego **cena** — ani dokumentacja, ani cennik jej nie
   podają. Bez ceny nie wpinamy go w CI (tak jak w #94).
5. **Plan Expo Starter ($19/mies.)** — czy akceptowalny dla E2E (Maestro nie działa na Free)?
6. **Push, Universal Links, Apple Pay** — czy są w roadmapie? Od tego zależy, jak wcześnie
   potrzebny jest test na fizycznym urządzeniu.
7. README podaje limit sesji EAS Simulator „30 min / 10 min bezczynności”, a dokumentacja Expo
   40 min (Free) / 115 min (płatne) i brak domyślnego limitu bezczynności. Czy to celowe
   ustawienia taska? Jeśli tak, warto to dopisać w README.
