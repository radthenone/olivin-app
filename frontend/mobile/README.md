# Olivin — aplikacja mobilna (Expo)

Aplikacja Expo (SDK 57, React Native 0.86, expo-router, expo-dev-client, NativeWind 4 + Tailwind 3)
działająca na **web, Androidzie i iOS**. Ten plik opisuje, jak ją uruchomić na każdej platformie,
jakie narzędzia do urządzeń mamy i co sprawdza CI.

Komendy `task` odpalasz z korzenia repo (`task --list` pokazuje wszystkie). Argumenty po `--`.

> **Nie podbijaj Tailwinda do v4.** NativeWind 4 działa tylko z Tailwindem 3 — patrz komentarz
> w `tailwind.config.js` i #72.

## Trzy warstwy sprawdzania aplikacji

| Warstwa          | Narzędzie                                       | Gdzie                | Co daje                                                                 |
| ---------------- | ----------------------------------------------- | -------------------- | ----------------------------------------------------------------------- |
| Smoke builda     | `task mobile:smoke` (job **Mobile smoke** w CI) | CI / dowolna maszyna | bundel Metro dla web, android, ios — łapie błędy Babel/Metro/NativeWind |
| Pętla dev        | Expo Device Hub (`expo-device-hub`)             | lokalnie             | sterowanie emulatorami/symulatorami i podgląd na żywo w przeglądarce    |
| Builde w chmurze | EAS Simulator                                   | chmura EAS           | iOS bez maca, weryfikacja buildów, sterowanie przez agentów             |

Narzędzia się nie wykluczają: smoke mówi „bundluje się”, device-hub i EAS Simulator mówią
„wstaje na urządzeniu”.

## Wymagania

| Cel              | Potrzebujesz                                                                                                       |
| ---------------- | ------------------------------------------------------------------------------------------------------------------ |
| Wszystko         | Bun (wersja z `frontend/package.json`), `task`, zależności: `task packages:frontend:sync`                          |
| Web              | tylko przeglądarka                                                                                                 |
| Android lokalnie | Android SDK z narzędziami `emulator` i `adb` w `PATH` (Android Studio albo `cmdline-tools`), AVD (domyślnie `S23`) |
| iOS lokalnie     | **macOS + Xcode** (symulatory iOS nie działają na Linuksie/Windowsie)                                              |
| iOS bez maca     | EAS Simulator — dostęp z waitlisty + konto Expo (`bunx eas-cli login`)                                             |

## Uruchomienie

### Web

```bash
cd frontend/mobile && bunx expo start --web
```

Albo `task mobile:metro` i klawisz `w` w terminalu Metro.

### Android (emulator)

```bash
task emulator:run -- S23                    # start AVD
task mobile:build:android -- emulator-5554  # raz: build i instalacja dev clienta
task mobile:run -- emulator-5554            # Metro + otwarcie dev clienta
```

`task mobile:run:clear` czyści cache Metro. Expo Go (bez natywnych modułów): `task mobile:run:go`.

### iOS (symulator, macOS)

```bash
cd frontend/mobile
bun run ios      # expo run:ios — prebuild, build w Xcode, instalacja na symulatorze
bun run start    # kolejne uruchomienia: samo Metro z dev clientem
```

Bez maca — patrz [EAS Simulator](#eas-simulator-chmura).

## Expo Device Hub (lokalnie)

[`expo-device-hub`](https://github.com/expo/expo-device-hub) to plugin Expo Dev Tools (wymaga
SDK 57+). Jest w `devDependencies`; nie ma kodu natywnego (platforma `devtools`), więc nie wpływa
na build aplikacji. Daje w przeglądarce: listę emulatorów/symulatorów, boot i shutdown, podgląd na
żywo, tap/swipe/pisanie, synchronizację jasnego/ciemnego motywu, zrzuty ekranu.

- **Z Metro:** `task mobile:metro` — w terminalu pojawi się link
  `Expo Device Hub: http://localhost:8081/_expo/plugins/expo-device-hub`.
- **Samodzielnie (bez Metro):** `task mobile:devices`.
- Zrzuty ekranu podglądu do katalogu: `EXPO_DEVICE_HUB_SCREENSHOT_DIRECTORY=/ścieżka`.

Wymagania jak przy lokalnym uruchomieniu: Android SDK (`emulator`, `adb`) dla Androida,
macOS + Xcode dla iOS. Web nie jest celem device-hubu — web oglądasz w zwykłej przeglądarce.

Strumień wideo idzie przez `node-datachannel` (natywny addon WebRTC). Jest w `trustedDependencies`
w `frontend/package.json` (bun czyta je z korzenia workspace), żeby `bun install` pobrał jego prebuilt binarkę — bez tego hub wstaje, ale nie pokazuje podglądu.

### Pętla diagnostyczna

Blokada z pobieraniem bundla (#54) jest zamknięta razem z wejściem SDK 57. Przy podobnym problemie
device-hub daje powtarzalną pętlę: `task mobile:metro` → boot emulatora z huba → otwarcie dev
clienta → obserwacja podglądu i logów Metro w jednym miejscu → `task mobile:metro:clear` i powtórka.
Zrzuty z `EXPO_DEVICE_HUB_SCREENSHOT_DIRECTORY` zostają jako ślad między próbami.

## EAS Simulator (chmura)

Simulatory iOS i emulatory Androida w chmurze EAS, stream do przeglądarki. Dostaje **gotowy build**
(`.app` / APK), nie lokalne Metro (dev build może się podpiąć do Metro przez tunel).

> **Wymaga dostępu.** Usługa jest w early access — dostęp tylko z waitlisty
> (<https://expo.dev/services/simulators>). Zapis to krok ręczny właściciela konta Expo. Do czasu
> dostępu taski poniżej padną na autoryzacji. **Nie ma tego w CI.**

Przygotowane:

- `eas.json` z profilami `remote-device` (instalowalny build: iOS `simulator: true`, Android
  `buildType: apk`) i `development-simulator` (to samo z `developmentClient: true`).
- Taski:

```bash
bunx eas-cli login                                    # raz
task mobile:eas:build:simulator -- ios                # albo android; wypisuje build id
BUILD_ID=<id> task mobile:eas:simulator -- ios        # sesja, max 30 min / 10 min bezczynności
task mobile:eas:simulator:stop
```

Przed pierwszym buildem trzeba podpiąć projekt EAS (`bunx eas-cli init`). `app.config.js` jest
dynamiczny, więc `eas init` nie dopisze `extra.eas.projectId` sam — wypisze wartość do wklejenia.

**Pierwszy build Androida** odpal interaktywnie, bez `--non-interactive` — EAS musi zapytać o
wygenerowanie keystore:

```bash
cd frontend/mobile && bunx eas-cli build --platform android --profile remote-device
```

Kolejne buildy (już z keystore na EAS) mogą iść przez `task mobile:eas:build:simulator -- android`.

Dev build przez tunel (hot reload w przeglądarce) — wg dokumentacji Expo:

```bash
bunx eas-cli build --platform ios --profile development-simulator --non-interactive
EXPO_UNSTABLE_TUNNEL_V2=1 bunx expo start --tunnel
bunx eas-cli simulator:start --platform ios --type agent-device --build-id <id> \
  --open-url "olivin://expo-development-client/?url=<zakodowany-url-metro>" --non-interactive
```

Android w EAS Simulator nie ma podglądu na żywo w przeglądarce — tylko sterowanie i zrzuty.
Dokumentacja: <https://docs.expo.dev/preview/eas-simulator/introduction>.

## Smoke w CI

Job **Mobile smoke** w `.github/workflows/ci.yml` na każdym PR i pushu na `dev`/`master`:

1. `bun install --frozen-lockfile`
2. `task mobile:smoke` — `expo export --platform all`: bundel Metro (Babel, NativeWind, Hermes) dla
   android i ios oraz statyczny eksport web (renderuje trasy w Node). Wynik w `dist/`
   (gitignored).
3. `task mobile:doctor` — `expo-doctor` (wersja przypięta w `package.json`): zgodność wersji paczek
   z SDK, konfiguracja. W CI bez kontroli wersji
   patchy (`EXPO_DOCTOR_SKIP_DEPENDENCY_VERSION_CHECK=1`) — porównuje z najnowszym wydaniem na npm, więc
   wynik zmieniałby się bez zmian w repo; patche podbijasz lokalnie (`bunx expo install --check`).
   Odpala się także po nieudanym bundlu, żeby jeden błąd nie zasłaniał drugiego.
   Wyjątki dla znanych, zaakceptowanych ostrzeżeń: klucz `expo.doctor` w `package.json`.

Job ma limit 20 minut.

Nie potrzebuje sekretów ani emulatora. **Nie sprawdza**, czy aplikacja wstaje na urządzeniu
(natywny build, moduły natywne, runtime) — to zostaje device-hubowi lokalnie albo EAS Simulatorowi.

## Słaby serwer (1 CPU)

Na małym VPS-ie **nie odpalaj lokalnie** ciężkich rzeczy: `task mobile:smoke` / `expo export`,
`expo prebuild`, Metro, `bun install` całego monorepo, pełnego lintu/typechecku frontendu, emulatora.
Maszyna potrafi się zawiesić. Smoke weryfikuje CI na PR — to jest dowód. Lokalnie zostaw lekkie
rzeczy: walidację YAML, `bunx prettier --check <plik>`, `tsc --noEmit` w jednym workspace. Gdy
zmieniasz zależności: `cd frontend && bun install --lockfile-only` aktualizuje sam `bun.lock`.

## Ograniczenia i otwarte pytania

- **Koszt EAS Simulator** — cennik niepubliczny; sesja nalicza zużycie, dopóki trwa. Przed jakimkolwiek
  wpięciem w CI trzeba go sprawdzić (taski mają limit 30 min / 10 min bezczynności).
- **EAS Simulator + Metro przez tunel** — tunel zmienia trasę ruchu; przy diagnozie problemów
  sieciowych lepiej lokalny emulator.
- **Smoke ≠ uruchomienie** — CI nie bootuje emulatora; zielony smoke nie gwarantuje, że aplikacja
  wstaje (natywne crashe, uprawnienia, runtime).
- **device-hub 0.x** — API i wymagania mogą się zmieniać między wersjami minor.
- Skill `eas-simulator` dla agentów — do rozważenia po otrzymaniu dostępu.
