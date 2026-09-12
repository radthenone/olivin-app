import { expect, test } from "@playwright/test";

const liveBackend = process.env.E2E_LIVE_BACKEND === "1";

/**
 * Strona główna pokazuje stan zdrowia backendu.
 *
 * Test patrzy na to, co widzi użytkownik: nagłówek i komunikat o stanie —
 * nie na strukturę komponentów ani nazwy klas. Odpowiedź /health/ jest
 * podstawiana, chyba że E2E_LIVE_BACKEND=1; wtedy sprawdzany jest cały
 * łańcuch aż do Django.
 */
test("home page shows the backend health status", async ({ page }) => {
  if (!liveBackend) {
    await page.route("**/health/", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          status: "healthy",
          services: {
            database: "healthy",
            redis: "healthy",
            storage: "healthy",
          },
        }),
      }),
    );
  }

  await page.goto("/");

  await expect(
    page.getByRole("heading", { level: 1, name: "Olivin" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { level: 2, name: "Stan backendu" }),
  ).toBeVisible();

  const status = page.getByRole("status");
  await expect(status).toBeVisible();
  await expect(status).toContainText("Backend odpowiada: healthy");
});
