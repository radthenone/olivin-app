import { expect, test, type Page } from "@playwright/test";

/**
 * Logowanie hasłem, sesja i wylogowanie na webie (#349).
 *
 * Domyślnie odpowiedzi allauth są podstawiane przez `page.route`, więc test
 * sprawdza cały łańcuch przeglądarka → Next → klient Orval → formularz bez
 * Django. `E2E_LIVE_BACKEND=1` wyłącza podstawianie i wymaga danych konta
 * w `E2E_AUTH_EMAIL` / `E2E_AUTH_PASSWORD` (opcjonalnie `E2E_AUTH_DISPLAY`).
 */
const liveBackend = process.env.E2E_LIVE_BACKEND === "1";
const liveEmail = process.env.E2E_AUTH_EMAIL ?? "";
const livePassword = process.env.E2E_AUTH_PASSWORD ?? "";
const liveDisplay = process.env.E2E_AUTH_DISPLAY ?? "";

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

function credentials() {
  if (liveBackend) {
    return { email: liveEmail, password: livePassword };
  }

  return { email: "jan@example.com", password: "tajne-haslo" };
}

function expectedDisplay() {
  return liveBackend ? liveDisplay : stubUser.display;
}

type StubbedRequests = { csrf?: string; email?: string; password?: string };

/**
 * Podstawia allauth w trybie przeglądarkowym: pierwszy GET sesji ustawia
 * ciasteczko CSRF, login zmienia stan, logout go czyści.
 */
async function stubAllauth(page: Page): Promise<StubbedRequests> {
  const seen: StubbedRequests = {};

  if (liveBackend) {
    return seen;
  }

  let authenticated = false;

  await page.route("**/_allauth/browser/v1/auth/session", async (route) => {
    if (route.request().method() === "DELETE") {
      authenticated = false;

      await route.fulfill({
        status: 401,
        headers: { "content-type": "application/json" },
        body: JSON.stringify(unauthBody),
      });
      return;
    }

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
    const request = route.request();
    const body = request.postDataJSON() as {
      email?: string;
      password?: string;
    };

    seen.csrf = request.headers()["x-csrftoken"];
    seen.email = body.email;
    seen.password = body.password;

    const { email, password } = credentials();
    const valid = body.email === email && body.password === password;

    authenticated = valid;

    await route.fulfill({
      status: valid ? 200 : 401,
      headers: { "content-type": "application/json" },
      body: JSON.stringify(
        valid
          ? authenticatedBody()
          : {
              status: 401,
              data: { flows: [{ id: "login" }] },
              meta: { is_authenticated: false },
              errors: [
                {
                  param: "password",
                  code: "email_password_mismatch",
                  message: "The password is incorrect.",
                },
              ],
            },
      ),
    });
  });

  // Wartości oglądamy w testach, nie w handlerze — wyjątek w route wiesza test.
  return seen;
}

async function fillLoginForm(page: Page, email: string, password: string) {
  await page.getByLabel("E-mail").fill(email);
  await page.getByLabel("Hasło").fill(password);
  await page.getByRole("button", { name: "Zaloguj" }).click();
}

test.beforeEach(() => {
  test.skip(
    liveBackend && (!liveEmail || !livePassword),
    "E2E_LIVE_BACKEND=1 wymaga E2E_AUTH_EMAIL i E2E_AUTH_PASSWORD.",
  );
});

test.describe("password login on the web", () => {
  test("logs in, shows the account name and keeps the session after reload", async ({
    page,
  }) => {
    const seen = await stubAllauth(page);
    const { email, password } = credentials();

    await page.goto("/pl/login");
    await fillLoginForm(page, email, password);

    const display = expectedDisplay();
    if (display) {
      await expect(page.getByText(display)).toBeVisible();
    }
    await expect(page.getByRole("button", { name: "Wyloguj" })).toBeVisible();

    if (!liveBackend) {
      expect(seen.email).toBe(email);
      expect(seen.password).toBe(password);
      // Klient przeglądarkowy allauth wymaga tokenu CSRF z ciasteczka.
      expect(seen.csrf).toBe("csrf-test");
    }

    await page.reload();

    if (display) {
      await expect(page.getByText(display)).toBeVisible();
    }
    await expect(page.getByRole("button", { name: "Wyloguj" })).toBeVisible();
    await expect(
      page.getByRole("link", { name: "Zaloguj się", exact: true }),
    ).toBeHidden();
  });

  test("shows a wrong password at the password field", async ({ page }) => {
    await stubAllauth(page);
    const { email } = credentials();

    await page.goto("/pl/login");
    await fillLoginForm(page, email, `${credentials().password}-zle`);

    await expect(
      page.getByText("Nieprawidłowy e-mail lub hasło."),
    ).toBeVisible();
    await expect(page.getByLabel("Hasło")).toHaveAttribute(
      "aria-invalid",
      "true",
    );
    await expect(
      page.getByRole("link", { name: "Zaloguj się", exact: true }),
    ).toBeVisible();
  });

  test("logs out and clears the account from the header", async ({ page }) => {
    await stubAllauth(page);
    const { email, password } = credentials();

    await page.goto("/pl/login");
    await fillLoginForm(page, email, password);
    await expect(page.getByRole("button", { name: "Wyloguj" })).toBeVisible();

    await page.getByRole("button", { name: "Wyloguj" }).click();

    await expect(
      page.getByRole("link", { name: "Zaloguj się", exact: true }),
    ).toBeVisible();
    await expect(page.getByRole("button", { name: "Wyloguj" })).toBeHidden();

    const display = expectedDisplay();
    if (display) {
      await expect(page.getByText(display)).toBeHidden();
    }
  });
});
