import { expect, test } from "@playwright/test";

/**
 * Kraj dostawy w profilu zalogowanego klienta na webie (#363, ADR 0035).
 *
 * Sprawdza:
 * 1. Zalogowany klient zmienia kraj w przełączniku „Wysyłka do” i profil dostaje zapis.
 * 2. Logowanie z innym krajem zapisanym w profilu przełącza walutę w sklepie.
 */
const liveBackend = process.env.E2E_LIVE_BACKEND === "1";

const stubUser = {
  id: 1,
  display: "Jan Jubiler",
  email: "jan@example.com",
  has_usable_password: true,
  username: "jan",
};

const unauthBody = {
  status: 401,
  data: { flows: [{ id: "login" }] },
  meta: { is_authenticated: false },
};

function authenticatedBody() {
  return {
    status: 200,
    data: { user: stubUser, methods: [] },
    meta: { is_authenticated: true },
  };
}

test.describe("Delivery country saved in customer profile (#363)", () => {
  test("zalogowany klient zmienia kraj i profil dostaje zapis", async ({
    page,
  }) => {
    test.skip(liveBackend, "Podstawianie odpowiedzi dotyczy trybu stub.");

    let patchedCountry: string | null = null;

    // Sesja zalogowanego klienta
    await page.route("**/_allauth/browser/v1/auth/session", async (route) => {
      await route.fulfill({
        status: 200,
        headers: {
          "content-type": "application/json",
          "set-cookie": "csrftoken=csrf-test; Path=/; SameSite=Lax",
        },
        body: JSON.stringify(authenticatedBody()),
      });
    });

    // Profil klienta
    await page.route("**/customers/profile/**", async (route) => {
      if (route.request().method() === "PATCH") {
        const body = route.request().postDataJSON() as {
          deliveryCountry?: string;
        };
        patchedCountry = body.deliveryCountry ?? null;
        await route.fulfill({
          status: 200,
          headers: { "content-type": "application/json" },
          body: JSON.stringify({
            id: "prof-1",
            deliveryCountry: patchedCountry,
          }),
        });
        return;
      }

      await route.fulfill({
        status: 200,
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          count: 1,
          next: null,
          previous: null,
          results: [{ id: "prof-1", deliveryCountry: "PL" }],
        }),
      });
    });

    await page.goto("/pl/products");

    const countrySelect = page.locator("#delivery-country-select");
    await expect(countrySelect).toBeVisible();
    await expect(countrySelect).toHaveValue("PL");

    // Zmiana kraju na Niemcy (DE)
    await countrySelect.selectOption("DE");
    await expect(countrySelect).toHaveValue("DE");

    // Profil klienta otrzymał żądanie zapisu nowego kraju
    await expect.poll(() => patchedCountry).toBe("DE");
  });

  test("błąd zapisu profilu pokazuje komunikat i nie cofa wyboru", async ({
    page,
  }) => {
    test.skip(liveBackend, "Podstawianie odpowiedzi dotyczy trybu stub.");

    await page.route("**/_allauth/browser/v1/auth/session", async (route) => {
      await route.fulfill({
        status: 200,
        headers: {
          "content-type": "application/json",
          "set-cookie": "csrftoken=csrf-test; Path=/; SameSite=Lax",
        },
        body: JSON.stringify(authenticatedBody()),
      });
    });

    await page.route("**/customers/profile/**", async (route) => {
      if (route.request().method() === "PATCH") {
        await route.fulfill({ status: 500, body: "{}" });
        return;
      }
      await route.fulfill({
        status: 200,
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          count: 1,
          next: null,
          previous: null,
          results: [{ id: "prof-1", deliveryCountry: "PL" }],
        }),
      });
    });

    await page.goto("/pl/products");

    const countrySelect = page.locator("#delivery-country-select");
    await countrySelect.selectOption("DE");

    await expect(
      page.getByRole("alert").filter({ hasText: /\S/ }),
    ).toBeVisible();
    await expect(countrySelect).toHaveValue("DE");
    const cookies = await page.context().cookies();
    expect(cookies.find((c) => c.name === "delivery_country")?.value).toBe(
      "DE",
    );
  });

  test("logowanie z innym krajem w profilu przełącza walutę", async ({
    page,
  }) => {
    test.skip(liveBackend, "Podstawianie odpowiedzi dotyczy trybu stub.");

    let authenticated = false;

    await page.route("**/_allauth/browser/v1/auth/session", async (route) => {
      await route.fulfill({
        status: authenticated ? 200 : 401,
        headers: {
          "content-type": "application/json",
          "set-cookie": "csrftoken=csrf-test; Path=/; SameSite=Lax",
        },
        body: JSON.stringify(authenticated ? authenticatedBody() : unauthBody),
      });
    });

    await page.route("**/_allauth/browser/v1/auth/login", async (route) => {
      authenticated = true;
      await route.fulfill({
        status: 200,
        headers: { "content-type": "application/json" },
        body: JSON.stringify(authenticatedBody()),
      });
    });

    // Profil klienta ma zapisane Niemcy (DE)
    await page.route("**/customers/profile/**", async (route) => {
      await route.fulfill({
        status: 200,
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          count: 1,
          next: null,
          previous: null,
          results: [{ id: "prof-1", deliveryCountry: "DE" }],
        }),
      });
    });

    // 1. Przed zalogowaniem na liście produktów obowiązuje domyślna waluta PLN
    await page.goto("/pl/products");
    await expect(page.getByText(/od 2.?450,00.?zł/).first()).toBeVisible();

    // 2. Przechodzimy na stronę logowania
    await page.goto("/pl/login");
    await page.getByLabel("E-mail").fill("jan@example.com");
    await page.getByLabel("Hasło").fill("tajne-haslo");
    await page.getByRole("button", { name: "Zaloguj" }).click();

    // 3. Po zalogowaniu przełącznik kraju przejmuje DE z profilu
    const countrySelect = page.locator("#delivery-country-select");
    await expect(countrySelect).toHaveValue("DE");

    // 4. W katalogu ceny przełączyły się na EUR
    await page.goto("/pl/products");
    await expect(page.getByText(/€/).first()).toBeVisible();
  });
});
