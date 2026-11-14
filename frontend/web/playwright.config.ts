import { readFileSync } from "node:fs";
import { join } from "node:path";
import { parseEnv } from "node:util";

import { defineConfig, devices } from "@playwright/test";

/**
 * Testy przeglądarkowe aplikacji webowej.
 *
 * Domyślnie katalog odpowiada stub API (`e2e/catalog-stub/`), uruchamiany jako
 * dodatkowy `webServer`, więc do przebiegu wystarczy sam Next — tak działa CI
 * bez Django. `E2E_LIVE_BACKEND=1` wyłącza stub i sprawdza prawdziwy łańcuch
 * przeglądarka → Next → Django; wymaga uruchomionego backendu
 * (`task backend:run` lub `task web:up`).
 */
const port =
  Number(process.env.E2E_PORT) ||
  // Żywy backend sprawdza CSRF Django, a dev domyślnie ufa portowi 3000
  // (`CSRF_TRUSTED_ORIGINS`). Testy z podstawianymi odpowiedziami zostają na
  // osobnym 3100, żeby nie wchodzić w paradę `task web:run`.
  (process.env.E2E_LIVE_BACKEND === "1" ? 3000 : 3100);
const liveBackend = process.env.E2E_LIVE_BACKEND === "1";
const stubPort = Number(process.env.E2E_STUB_PORT) || 3200;
const stubUrl = `http://localhost:${stubPort}`;
// Serwerowy transport katalogu nie idzie przez ciasteczka sesji, więc jego
// adres jest osobną zmienną od `NEXT_PUBLIC_BACKEND_URL`.
const catalogApiUrl = liveBackend
  ? (process.env.CATALOG_API_URL ?? "http://127.0.0.1:8020")
  : stubUrl;
// localhost, nie 127.0.0.1: Next w trybie deweloperskim blokuje żądania
// o zasoby z innego originu niż ten, na którym nasłuchuje (allowedDevOrigins),
// a bez zasobów strona nigdy się nie hydratuje.
const baseURL = `http://localhost:${port}`;
// W CI testy idą na buildzie produkcyjnym. `next dev` z Cache Components
// hydratuje wolno i w pierwszym podejściu akcje testu ścigały się z hydracją
// (#357). Next i tak zaleca e2e na buildzie produkcyjnym.
const prodServer = !!process.env.CI || process.env.E2E_PROD === "1";
// `next build` i `next start` nie czytają `.env.development`, więc te same
// wartości co w dev podajemy jawnie. Zmienna z powłoki wygrywa z plikiem,
// tak jak w Next.
const devFileEnv = prodServer
  ? Object.fromEntries(
      Object.entries(
        parseEnv(readFileSync(join(__dirname, ".env.development"), "utf8")),
      ).map(([key, value]): [string, string] => [
        key,
        process.env[key] ?? value ?? "",
      ]),
    )
  : {};

export default defineConfig({
  testDir: "./e2e",
  // Testy jednostkowe stuba (`bun:test`) nie są specami Playwright.
  testIgnore: ["**/catalog-stub/**"],
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["github"], ["list"]] : "list",
  use: {
    baseURL,
    trace: "on-first-retry",
    // Zrzut po porażce trafia do artefaktu CI razem z `error-context.md`.
    screenshot: "only-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    ...(liveBackend
      ? []
      : [
          {
            // Stub katalogu wstaje pierwszy; Next dostaje jego adres przez env.
            command: "bun run e2e/catalog-stub/server.ts",
            url: `${stubUrl}/health/`,
            reuseExistingServer: !process.env.CI,
            timeout: 30_000,
            stdout: "pipe" as const,
          },
        ]),
    {
      // Osobny port, żeby test nie wchodził w paradę `task web:run` na 3000.
      command: prodServer
        ? `bun run build && bun run start --port ${port}`
        : `bun run dev --port ${port}`,
      url: baseURL,
      reuseExistingServer: !process.env.CI,
      // Build produkcyjny trwa dłużej niż start serwera deweloperskiego.
      timeout: prodServer ? 300_000 : 120_000,
      env: { ...devFileEnv, CATALOG_API_URL: catalogApiUrl },
      // Logi Next (status żądań, błędy kompilacji) trafiają do wyjścia testu —
      // bez tego timeout webServera w CI nie mówi, na czym utknął.
      stdout: "pipe",
    },
  ],
});
