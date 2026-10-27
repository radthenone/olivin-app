import { expect, test, type Page } from "@playwright/test";

/**
 * Logowanie jednorazowym kodem na webie (#352).
 *
 * Odpowiedzi allauth są podstawiane przez `page.route`, więc test sprawdza
 * cały łańcuch przeglądarka → Next → klient Orval → formularz bez Django.
 * W trybie `E2E_LIVE_BACKEND=1` kod trzeba odebrać z prawdziwej wiadomości,
 * dlatego ten plik się wtedy pomija.
 */

const liveBackend = process.env.E2E_LIVE_BACKEND === "1";

const stubUser = {
  id: 9,
  display: "Kod Klient",
  email: "kod@example.com",
  has_usable_password: true,
  username: "kod",
};

const validCode = "ABC123";

const unauthBody = {
  status: 401,
  data: { flows: [{ id: "login" }] },
  meta: { is_authenticated: false },
};

/** Zamówienie kodu zostawia w sesji oczekujący etap `login_by_code`. */
function pendingCodeBody() {
  return {
    status: 401,
    data: { flows: [{ id: "login_by_code" }] },
    meta: { is_authenticated: false },
  };
}

function authenticatedBody() {
  return {
    status: 200,
    data: { user: stubUser, methods: [] },
    meta: { is_authenticated: true },
  };
}

type SeenRequests = {
  csrf?: string;
  email?: string;
  code?: string;
  requestCalls: number;
};

type StubOptions = {
  confirmStatus?: number;
  confirmBody?: unknown;
};

/**
 * Podstawia sesję, zamówienie kodu i potwierdzenie kodu w trybie
 * przeglądarkowym. Sesja loguje się dopiero po przyjęciu kodu.
 */
async function stubAllauth(
  page: Page,
  options: StubOptions = {},
): Promise<SeenRequests> {
  const seen: SeenRequests = { requestCalls: 0 };
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

  await page.route(
    "**/_allauth/browser/v1/auth/code/request",
    async (route) => {
      const request = route.request();

      seen.requestCalls += 1;
      seen.csrf = request.headers()["x-csrftoken"];
      seen.email = (request.postDataJSON() as { email?: string }).email;

      await route.fulfill({
        status: 401,
        headers: { "content-type": "application/json" },
        body: JSON.stringify(pendingCodeBody()),
      });
    },
  );

  await page.route(
    "**/_allauth/browser/v1/auth/code/confirm",
    async (route) => {
      const request = route.request();

      seen.code = (request.postDataJSON() as { code?: string }).code;

      const status = options.confirmStatus ?? 200;
      if (status === 200) {
        authenticated = true;
      }

      await route.fulfill({
        status,
        headers: { "content-type": "application/json" },
        body: JSON.stringify(
          options.confirmBody ??
            (status === 200 ? authenticatedBody() : unauthBody),
        ),
      });
    },
  );

  // Wartości oglądamy w testach, nie w handlerze — wyjątek w route wiesza test.
  return seen;
}

async function requestCode(page: Page, email: string) {
  await page.goto("/pl/login/code");
  await page.getByLabel("E-mail", { exact: true }).fill(email);
  await page.getByRole("button", { name: "Wyślij kod" }).click();
}

test.beforeEach(() => {
  test.skip(
    liveBackend,
    "Logowanie kodem na żywym backendzie wymaga kodu z maila.",
  );
});

test.describe("login by email code on the web", () => {
  test("sends the code and moves to the code screen", async ({ page }) => {
    const seen = await stubAllauth(page);

    await requestCode(page, stubUser.email);

    await expect(page).toHaveURL(/\/pl\/login\/code\/confirm$/);
    await expect(
      page.getByRole("heading", { name: "Wpisz kod z e-maila" }),
    ).toBeVisible();
    expect(seen.email).toBe(stubUser.email);
    expect(seen.csrf).toBe("csrf-test");
  });

  test("logs in with a valid code and shows the account name", async ({
    page,
  }) => {
    const seen = await stubAllauth(page);

    await requestCode(page, stubUser.email);
    await page.getByLabel("Kod logowania").fill(validCode);
    await page.getByRole("button", { name: "Zaloguj kodem" }).click();

    await expect(page.getByText(stubUser.display)).toBeVisible();
    await expect(page.getByRole("button", { name: "Wyloguj" })).toBeVisible();
    await expect(
      page.getByRole("link", { name: "Zaloguj się", exact: true }),
    ).toBeHidden();
    expect(seen.code).toBe(validCode);
  });

  test("shows a readable error for a wrong code", async ({ page }) => {
    await stubAllauth(page, {
      confirmStatus: 400,
      confirmBody: {
        status: 400,
        errors: [
          {
            param: "code",
            code: "incorrect_code",
            message: "Incorrect code.",
          },
        ],
      },
    });

    await requestCode(page, stubUser.email);
    await page.getByLabel("Kod logowania").fill("ZLE999");
    await page.getByRole("button", { name: "Zaloguj kodem" }).click();

    await expect(
      page.getByText("Kod jest nieprawidłowy lub wygasł."),
    ).toBeVisible();
    await expect(
      page.getByRole("link", { name: "Zaloguj się", exact: true }),
    ).toBeVisible();
  });

  test("shows the same error when the code has expired", async ({ page }) => {
    await stubAllauth(page, {
      confirmStatus: 409,
      confirmBody: { status: 409 },
    });

    await requestCode(page, stubUser.email);
    await page.getByLabel("Kod logowania").fill(validCode);
    await page.getByRole("button", { name: "Zaloguj kodem" }).click();

    await expect(
      page.getByText("Kod jest nieprawidłowy lub wygasł."),
    ).toBeVisible();
    await expect(
      page.getByRole("link", { name: "Zaloguj się", exact: true }),
    ).toBeVisible();
  });
});
