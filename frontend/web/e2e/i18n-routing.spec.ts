import { expect, test, type Page } from "@playwright/test";

/**
 * Routing języka na webie (ADR 0035).
 *
 * Test dotyka wyłącznie publicznego zachowania: adresu, nagłówków i tekstów,
 * które widzi klient. Odpowiedź zdrowia jest podstawiana, więc CI nie potrzebuje
 * Django; `E2E_LIVE_BACKEND=1` sprawdza pełny łańcuch z prawdziwym backendem.
 */
const healthPayload = {
  status: "healthy",
  services: {
    database: "healthy",
    redis: "healthy",
    storage: "healthy",
  },
};

async function stubHealth(page: Page) {
  if (process.env.E2E_LIVE_BACKEND === "1") {
    return;
  }

  await page.route("**/health/", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(healthPayload),
    }),
  );
}

// `Accept-Language` ustawiamy przez `locale` kontekstu: Chromium nadpisuje nim
// nagłówek z `setExtraHTTPHeaders`, a Playwright Test domyślnie ma `en-US`.
test.describe("language prefix routing", () => {
  test.describe("with a Polish browser", () => {
    test.use({ locale: "pl-PL" });

    test("redirects / by the language cookie before Accept-Language", async ({
      page,
    }) => {
      await page.goto("/pl");
      const origin = new URL(page.url()).origin;

      await page
        .context()
        .addCookies([{ name: "NEXT_LOCALE", value: "en", url: origin }]);

      await page.goto("/");

      await expect(page).toHaveURL(`${origin}/en`);
    });
  });

  test.describe("with an English browser", () => {
    test.use({ locale: "en-US" });

    test("redirects / by Accept-Language when there is no cookie", async ({
      page,
    }) => {
      await page.goto("/");

      await expect(page).toHaveURL(/\/en$/);
    });
  });

  test.describe("with a German browser", () => {
    test.use({ locale: "de-DE" });

    test("redirects / to Polish when the language is unsupported", async ({
      page,
    }) => {
      await page.goto("/");

      await expect(page).toHaveURL(/\/pl$/);
    });
  });
});

test.describe("technical paths", () => {
  for (const path of [
    "/api/probe",
    "/.well-known/assetlinks.json",
    "/robots.txt",
    "/sitemap.xml",
  ]) {
    test(`does not redirect ${path}`, async ({ page }) => {
      const response = await page.request.get(path, { maxRedirects: 0 });

      expect(response.status()).toBe(404);
      expect(response.headers()["location"]).toBeUndefined();
    });
  }
});

test.describe("API client language", () => {
  test("sends Accept-Language from the interface locale", async ({ page }) => {
    await stubHealth(page);
    const healthRequest = page.waitForRequest("**/health/");

    await page.goto("/en");

    const request = await healthRequest;
    expect(request.headers()["accept-language"]).toBe("en");
  });
});

test.describe("health page translations", () => {
  test("shows Polish texts under /pl", async ({ page }) => {
    await stubHealth(page);

    await page.goto("/pl");

    await expect(
      page.getByRole("heading", { level: 2, name: "Stan backendu" }),
    ).toBeVisible();
    await expect(page.getByRole("status")).toContainText(
      "Backend odpowiada: healthy",
    );
    await expect(page.getByText("Baza danych")).toBeVisible();
  });

  test("shows English texts under /en", async ({ page }) => {
    await stubHealth(page);

    await page.goto("/en");

    await expect(
      page.getByRole("heading", { level: 2, name: "Backend status" }),
    ).toBeVisible();
    await expect(page.getByRole("status")).toContainText(
      "Backend is responding: healthy",
    );
    await expect(page.getByText("Database")).toBeVisible();
  });
});
