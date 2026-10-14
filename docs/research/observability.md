# Raportowanie błędów i logi produkcyjne — research

> Stan na: 2026-10-14. Źródła pierwotne (dokumentacja producentów) podlinkowane przy każdym twierdzeniu.
> Kontekst: mały sklep z biżuterią — Next.js 16 (web), Expo SDK 57 / RN 0.86 (EAS Build, Android + iOS),
> Django + Celery worker + Celery beat, jeden VPS, `docker-compose.prod.yml` (gunicorn, bez konfiguracji `logging:`).

## TL;DR

- **Błędy:** Sentry SaaS, plan Developer (darmowy), **region EU (Frankfurt)**. Najmniej pracy i jedyna opcja, w której
  source mapy z EAS Build i Next.js „po prostu działają” przez oficjalne pluginy.
- **GlitchTip self-hosted** jest realną alternatywą (256–512 MB RAM), ale source mapy dla Next.js/Expo to niepewny teren.
- **Sentry self-hosted** odpada: min. 4 rdzenie i 16 GB RAM.
- **Logi:** bez Loki/Grafany. Ustawić driver `local` (rotacja) i czytać `docker compose logs`. Loki dopiero, gdy pojawi się realna potrzeba przeszukiwania.

---

## 1. Sentry SaaS

### Limity planów ([sentry.io/pricing](https://sentry.io/pricing/))

| | Developer (free) | Team |
|---|---|---|
| Cena | $0 | $26/mies. (rozliczenie roczne) |
| Użytkownicy | **1** | bez limitu |
| Błędy | 5k / mies. | 50k / mies. |
| Spany (tracing) | 5M | 5M |
| Session Replay | 50 | 50 |
| Logi | 5 GB | 5 GB |
| Załączniki | 1 GB | 1 GB |
| Retencja | 30 dni | do 90 dni |

Po przekroczeniu kwoty zdarzenia **nie są przyjmowane** (są odrzucane, nie dopłaca się automatycznie); dostępna jest
Spike Protection oraz limity per DSN ([docs: quotas](https://docs.sentry.io/pricing/quotas/)). Dla małego sklepu 5k błędów
to dużo — pod warunkiem, że jeden zapętlony błąd nie zje kwoty (stąd rate limit per projekt).

Ograniczenie praktyczne: **1 użytkownik** na Developerze — jeśli ktoś poza właścicielem ma widzieć błędy, potrzebny Team.

### Rezydencja danych / RODO

- Region wybierany **przy tworzeniu organizacji**: US (Iowa) albo **EU (Frankfurt)**; **nie da się go zmienić później**
  ([docs: data storage location](https://docs.sentry.io/organization/data-storage-location/)).
- W EU zostają: eventy błędów, transakcje/spany, logi, release'y, source mapy, replaye i ich backupy. **Zawsze w US**:
  konta użytkowników, ustawienia organizacji, metadane projektów, klucze DSN, check-iny cronów, tokeny, dane z supportu
  (tamże).
- Region EU jest dostępny na wszystkich planach, łącznie z darmowym Developer, bez dopłaty
  ([changelog Sentry](https://docs.sentry.io/changelog/data-storage-location-in-germany-is-generally-available/)).
- DPA z SCC (decyzja KE 2021/914) i listą podprocesorów: [sentry.io/legal/dpa](https://sentry.io/legal/dpa/5.0.0),
  [sentry.io/legal/subprocessors](https://sentry.io/legal/subprocessors/). Sentry (Functional Software, Inc.) to firma z USA —
  nawet z regionem EU jest to transfer/podprocesor z USA, który trzeba wpisać do polityki prywatności i rejestru czynności.

### Scrubbing PII

Po stronie SDK (Python) — domyślnie, bez `send_default_pii`
([docs: data collected](https://docs.sentry.io/platforms/python/data-management/data-collected/)):
- **nie** wysyła IP, ciasteczek ani danych zalogowanego użytkownika;
- nagłówki wysyła, ale filtruje wrażliwe; surowe body requestów usuwa;
- **zawsze** wysyła pełny URL z query stringiem → nie wolno trzymać PII (e-mail, token resetu) w query stringu.
- Dokumentacja opisuje też nowsze `data_collection` — **uwaga**: przekazanie tego słownika przełącza nieustawione kategorie
  na *bardziej* permisywne wartości domyślne (ciasteczka, query). Bezpieczniej zostać przy domyślnym `send_default_pii=False`.

Po stronie JS/RN: hooki `beforeSend` / `beforeSendTransaction` do wycięcia danych przed wysłaniem
([docs RN: sensitive data](https://docs.sentry.io/platforms/react-native/data-management/sensitive-data/)).

Po stronie serwera Sentry ([docs: server-side scrubbing](https://docs.sentry.io/security-legal-pii/scrubbing/server-side-scrubbing/)):
Data Scrubber domyślnie włączony (numery kart, pola z `password`, `secret`, `token`…), opcja „Prevent storing IP addresses”
(geo nadal wyliczane z IP, chyba że reguła Advanced Data Scrubbing), własne Sensitive Fields — warto dodać np. `email`,
`phone`, `address`, `postal_code`.

Session Replay: **nie włączać** na start (50 replayów i tak nic nie da, a nagrywanie checkoutu to dodatkowe ryzyko RODO).

### Integracja w naszym stacku

- **Django + Celery** (`sentry-sdk`): integracja Celery włącza się automatycznie i łapie wyjątki tasków; monitorowanie
  Celery Beat jako Sentry Crons wymaga `monitor_beat_tasks=True`
  ([docs: Celery](https://docs.sentry.io/platforms/python/integrations/celery/)). Uwaga: check-iny cronów są przechowywane w US.
- **Next.js** (`@sentry/nextjs`): wizard `npx @sentry/wizard@latest -i nextjs` tworzy `instrumentation-client.ts`,
  `sentry.server.config.ts`, `sentry.edge.config.ts`, `instrumentation.ts` i owija config w `withSentryConfig`;
  `tunnelRoute` omija adblockery ([docs: Next.js](https://docs.sentry.io/platforms/javascript/guides/nextjs/)).
  Source mapy z Turbopack są wysyłane po buildzie, wymagają `@sentry/nextjs@10.13.0+` i `next@15.4.1+`; client-side source
  mapy są domyślnie kasowane po uploadzie (`deleteSourcemapsAfterUpload: true`)
  ([docs: Next.js source maps](https://docs.sentry.io/platforms/javascript/guides/nextjs/sourcemaps/)).
  Dokumentacja wymienia „Next.js 14+” — **jawnego potwierdzenia dla Next 16 na tych stronach nie znalazłem**.
- **Expo** (`@sentry/react-native`): `npx expo install @sentry/react-native`, plugin `@sentry/react-native/expo` w `app.json`
  (`url`, `project`, `organization`), `getSentryExpoConfig` w `metro.config.js` (Debug IDs), `SENTRY_AUTH_TOKEN` jako sekret EAS
  ([docs: Expo](https://docs.sentry.io/platforms/react-native/manual-setup/expo/)). Source mapy release'owych buildów EAS
  wysyłają się **automatycznie**; dla **EAS Update** ręcznie: `npx @sentry/expo-upload-sourcemaps dist` (od
  `@sentry/react-native` 8.9.0), bez powiązania z release
  ([docs: Expo source maps](https://docs.sentry.io/platforms/react-native/sourcemaps/uploading/expo/)).
  Kompatybilności z Expo SDK 57 / RN 0.86 nie zweryfikowałem — sprawdzić przy instalacji (`npx expo install` dobierze wersję).

---

## 2. GlitchTip (self-hosted lub hosted)

- **Zasoby:** Postgres 14+; Valkey/Redis **opcjonalny** (bez niego kolejka/cache w Postgresie); zalecane **512 MB RAM**,
  minimum 256 MB w trybie all-in-one (`GLITCHTIP_EMBED_WORKER=True`); ok. 30 GB dysku na 1M eventów/mies.
  ([docs: install](https://glitchtip.com/documentation/install)). Możemy użyć istniejącego `olivin-postgres` (osobna baza).
- **Retencja:** `GLITCHTIP_RETENTION_DAYS` (domyślnie 90), `GLITCHTIP_EVENT_HOT_DAYS` (30) (tamże).
- **Funkcje:** błędy, uptime monitoring, performance (transakcje, spany, p50/p95 per grupa), logi
  ([docs](https://glitchtip.com/documentation), [docs: performance](https://glitchtip.com/documentation/performance)).
  Brak Session Replay i profilowania w dokumentacji.
- **Source mapy — główne ryzyko:** GlitchTip ma własne `glitchtip-cli sourcemaps inject` + `upload --release`
  ([docs: CLI](https://glitchtip.com/documentation/cli)), ale **nie dokumentuje** zgodności z pluginami Sentry
  (`withSentryConfig`, plugin Expo, `@sentry/expo-upload-sourcemaps`). Zgłoszenie
  [glitchtip-backend#342](https://gitlab.com/glitchtip/glitchtip-backend/-/issues/342) (2024) pokazuje brakujący endpoint
  przy `sentry-cli`. W praktyce: automatyczny upload z EAS Build najpewniej trzeba zastąpić własnym krokiem w CI —
  do sprawdzenia spike'iem.
- **Hosted GlitchTip:** free 1000 eventów/mies., $15/100k, $50/500k; **instancja EU w Niemczech na wszystkich planach**
  ([glitchtip.com/pricing](https://glitchtip.com/pricing)).
- **RODO self-hosted:** dane nie opuszczają naszego VPS — najprostsza historia prywatności, ale backup, aktualizacje
  i bezpieczeństwo kolejnej aplikacji webowej (panel z danymi błędów) są na nas.

## 3. Sentry self-hosted

Minimum **4 rdzenie, 16 GB RAM + 16 GB swap** (zalecane 32 GB), 20 GB dysku; licencja FSL
([develop.sentry.dev/self-hosted](https://develop.sentry.dev/self-hosted/)). Na jednym VPS obok sklepu — **odpada**.

---

## 4. Logi produkcyjne (Django / kontenery)

Stan obecny: `docker-compose.prod.yml` nie ustawia `logging:`. Domyślny driver to `json-file`, który
**domyślnie nie rotuje** logów ([docs Docker: configure](https://docs.docker.com/engine/logging/configure/)) → przy
dłuższym działaniu realne ryzyko zapchania dysku.

**Minimum (zalecane):** driver `local` — rotacja domyślnie, 20 MB × 5 plików, kompresja, ok. 100 MB na kontener
([docs Docker: local](https://docs.docker.com/engine/logging/drivers/local/)). Globalnie w `/etc/docker/daemon.json`
(`{"log-driver": "local"}`, restart dockera, dotyczy nowych kontenerów) albo per serwis w compose:

```yaml
logging:
  driver: local
  options: { max-size: "20m", max-file: "5" }
```

Odczyt: `docker compose logs -f --since 1h olivin-django`. Django/gunicorn/Celery powinny pisać na stdout/stderr;
gunicorn domyślnie loguje błędy na stderr, a access logu **nie** włącza (`--access-logfile -`)
([gunicorn settings](https://docs.gunicorn.org/en/stable/settings.html)).

**journald** — alternatywa, jeśli host ma systemd: logi trafiają do `journalctl` z retencją sterowaną przez journald.
Dla nas nie daje przewagi nad `local` (ten sam brak wyszukiwania między kontenerami).

**Loki + Grafana** — tylko gdy faktycznie potrzebne wyszukiwanie/alerty po logach. Docker driver Lokiego trzyma logi
w pamięci, gubi je przy niedostępnym Lokim, może blokować daemona; Grafana zaleca Alloy zamiast drivera
([docs Loki: docker driver](https://grafana.com/docs/loki/latest/send-data/docker-driver/)). To 2–3 dodatkowe kontenery
do utrzymania — nadmiar na ten etap. Pośrednia opcja: Sentry Logs (5 GB w planie free) zamiast własnego Lokiego.

**PII w logach:** access log zawiera IP i URL-e (dane osobowe wg RODO) — rotacja ok. 100 MB/kontener daje naturalnie
krótką retencję; nie logować body requestów ani danych zamówień.

---

## Rekomendacja

1. **Sentry SaaS, Developer, region EU** — jedna organizacja, trzy projekty (web, mobile, backend).
   `send_default_pii=False` / brak `sendDefaultPii`, Data Scrubber + „Prevent storing IP addresses” + własne Sensitive Fields,
   bez Session Replay, `tracesSampleRate` niski (np. 0.1) albo 0 na start, rate limit per DSN.
2. Sentry wpisać do polityki prywatności jako podprocesor (US, SCC/DPF) i zaakceptować DPA.
3. Logi: `logging: driver: local` w `docker-compose.prod.yml` + `--access-logfile -` w gunicornie. Nic więcej.
4. Plan B (gdy właściciel nie chce podmiotu z USA): **hosted GlitchTip EU** lub self-hosted GlitchTip all-in-one
   na istniejącym Postgresie — po spike'u z uploadem source map z EAS i Next.js.

## Pytania otwarte do właściciela

1. Czy dopuszczasz podprocesora z USA (Sentry, nawet z danymi w Frankfurcie)? Jeśli nie → GlitchTip.
2. Ile osób ma widzieć błędy? Więcej niż 1 → Sentry Team ($26/mies.) lub GlitchTip.
3. Jaki jest rozmiar VPS (RAM/dysk)? Decyduje o sensowności self-hosted GlitchTip.
4. Czy potrzebujesz alertów (e-mail/Slack) poza samym zbieraniem błędów? Kto je odbiera?
5. Czy chcesz monitorować Celery Beat (Sentry Crons; check-iny przechowywane w US)?
6. Czy planujesz EAS Update (OTA)? Wtedy potrzebny dodatkowy krok uploadu source map w CI.
7. Uboczne spostrzeżenie: `docker-compose.prod.yml` ładuje pliki env z `./.envs/dev/backend/*` — czy to zamierzone?
