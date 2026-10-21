import { defineConfig, devices } from "@playwright/test";

/**
 * Testy przeglądarkowe aplikacji webowej.
 *
 * Domyślnie odpowiedź backendu jest podstawiana w teście (patrz e2e/), więc
 * do przebiegu wystarczy sam Next — tak działa CI. `E2E_LIVE_BACKEND=1`
 * wyłącza podstawianie i sprawdza prawdziwy łańcuch przeglądarka → Next →
 * Django; wymaga uruchomionego backendu (`task backend:run` lub `task web:up`).
 */
const port =
  Number(process.env.E2E_PORT) ||
  // Żywy backend sprawdza CSRF Django, a dev domyślnie ufa portowi 3000
  // (`CSRF_TRUSTED_ORIGINS`). Testy z podstawianymi odpowiedziami zostają na
  // osobnym 3100, żeby nie wchodzić w paradę `task web:run`.
  (process.env.E2E_LIVE_BACKEND === "1" ? 3000 : 3100);
// localhost, nie 127.0.0.1: Next w trybie deweloperskim blokuje żądania
// o zasoby z innego originu niż ten, na którym nasłuchuje (allowedDevOrigins),
// a bez zasobów strona nigdy się nie hydratuje.
const baseURL = `http://localhost:${port}`;

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["github"], ["list"]] : "list",
  use: {
    baseURL,
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    // Osobny port, żeby test nie wchodził w paradę `task web:run` na 3000.
    command: `bun run dev --port ${port}`,
    url: baseURL,
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
    // Logi Next (status żądań, błędy kompilacji) trafiają do wyjścia testu —
    // bez tego timeout webServera w CI nie mówi, na czym utknął.
    stdout: "pipe",
  },
});
