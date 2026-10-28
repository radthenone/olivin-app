import { expect, test, type Page } from "@playwright/test";

/**
 * Reset hasła kodem z e-maila na webie (#353, ADR 0038).
 *
 * Odpowiedzi allauth są podstawiane przez `page.route`, więc test sprawdza
 * cały łańcuch przeglądarka → Next → klient Orval → formularz bez Django.
 * Resetu nie da się powtórzyć na żywym backendzie (kod przychodzi prawdziwą
 * wiadomością), dlatego w trybie `E2E_LIVE_BACKEND=1` ten plik się pomija.
 */

const liveBackend = process.env.E2E_LIVE_BACKEND === "1";

const EMAIL = "klient@example.com";
const CODE = "ABC123";
const NEW_PASSWORD = "nowe-haslo-123";

const stubUser = {
  id: 9,
  display: EMAIL,
  email: EMAIL,
  has_usable_password: true,
  username: "klient",
};

const unauthBody = {
  status: 401,
  data: { flows: [{ id: "login" }] },
  meta: { is_authenticated: false },
};

/** Prośba o reset kodem kończy się oczekującym etapem w sesji. */
function pendingResetBody() {
  return {
    status: 401,
    data: { flows: [{ id: "password_reset_by_code", is_pending: true }] },
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
  request?: Record<string, unknown>;
  reset?: Record<string, unknown>;
  requestCalls: number;
  resetCalls: number;
};

type StubOptions = {
  requestStatus?: number;
  requestBody?: unknown;
  resetStatus?: number;
  resetBody?: unknown;
};

/**
 * Podstawia sesję, prośbę o reset i ustawienie hasła w trybie przeglądarkowym.
 *
 * Sesja startuje jako niezalogowana. Po resecie zakończonym statusem 200
 * backend loguje klienta, więc stub sesji przełącza się na zalogowaną.
 */
async function stubAllauth(
  page: Page,
  options: StubOptions = {},
): Promise<{ seen: SeenRequests }> {
  const seen: SeenRequests = { requestCalls: 0, resetCalls: 0 };
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
    "**/_allauth/browser/v1/auth/password/request",
    async (route) => {
      const request = route.request();

      seen.requestCalls += 1;
      seen.csrf = request.headers()["x-csrftoken"];
      seen.request = request.postDataJSON() as Record<string, unknown>;

      await route.fulfill({
        status: options.requestStatus ?? 401,
        headers: { "content-type": "application/json" },
        body: JSON.stringify(options.requestBody ?? pendingResetBody()),
      });
    },
  );

  await page.route(
    "**/_allauth/browser/v1/auth/password/reset",
    async (route) => {
      const request = route.request();

      seen.resetCalls += 1;
      seen.csrf = request.headers()["x-csrftoken"];
      seen.reset = request.postDataJSON() as Record<string, unknown>;

      const status = options.resetStatus ?? 401;
      if (status === 200) {
        authenticated = true;
      }

      await route.fulfill({
        status,
        headers: { "content-type": "application/json" },
        body: JSON.stringify(
          options.resetBody ??
            (status === 200
              ? authenticatedBody()
              : {
                  status: 401,
                  data: { flows: [{ id: "login" }] },
                  meta: { is_authenticated: false },
                }),
        ),
      });
    },
  );

  return { seen };
}

test.beforeEach(() => {
  test.skip(
    liveBackend,
    "Reset hasła wymaga podstawionych odpowiedzi allauth (kod z e-maila).",
  );
});

test.describe("password reset by code on the web", () => {
  test("requests a code and moves to the code form without a token in the address", async ({
    page,
  }) => {
    const { seen } = await stubAllauth(page);

    await page.goto("/pl/reset-password");
    await page.getByLabel("E-mail", { exact: true }).fill(EMAIL);
    await page.getByRole("button", { name: "Wyślij kod" }).click();

    await expect(page).toHaveURL(/\/pl\/reset-password\/confirm$/);
    await expect(
      page.getByRole("heading", { name: "Ustaw nowe hasło" }),
    ).toBeVisible();

    expect(seen.csrf).toBe("csrf-test");
    expect(seen.request).toEqual({ email: EMAIL });
    expect(page.url()).not.toMatch(/token|code/i);
  });

  test("sets the password and sends the client to sign in when allauth returns 401", async ({
    page,
  }) => {
    const { seen } = await stubAllauth(page);

    await page.goto("/pl/reset-password/confirm");
    await page.getByLabel("Kod z e-maila").fill(CODE);
    await page.getByLabel("Nowe hasło").fill(NEW_PASSWORD);
    await page.getByRole("button", { name: "Ustaw hasło" }).click();

    await expect(page).toHaveURL(/\/pl\/login$/);
    expect(seen.reset).toEqual({ key: CODE, password: NEW_PASSWORD });
    expect(page.url()).not.toMatch(/token|code/i);
  });

  test("returns to the shop already signed in when allauth logs the client in", async ({
    page,
  }) => {
    await stubAllauth(page, { resetStatus: 200 });

    await page.goto("/pl/reset-password/confirm");
    await page.getByLabel("Kod z e-maila").fill(CODE);
    await page.getByLabel("Nowe hasło").fill(NEW_PASSWORD);
    await page.getByRole("button", { name: "Ustaw hasło" }).click();

    await expect(page).toHaveURL(/\/pl$/);
    await expect(
      page.getByText(`Zalogowano jako ${stubUser.display}`),
    ).toBeVisible();
  });

  test("shows a wrong or expired code at the code field", async ({ page }) => {
    await stubAllauth(page, {
      resetStatus: 400,
      resetBody: {
        status: 400,
        errors: [
          {
            param: "key",
            code: "token_invalid",
            message: "The password reset token was invalid.",
          },
        ],
      },
    });

    await page.goto("/pl/reset-password/confirm");
    await page.getByLabel("Kod z e-maila").fill("000000");
    await page.getByLabel("Nowe hasło").fill(NEW_PASSWORD);
    await page.getByRole("button", { name: "Ustaw hasło" }).click();

    await expect(
      page.getByText("Kod jest nieprawidłowy lub wygasł."),
    ).toBeVisible();
    await expect(page.getByLabel("Kod z e-maila")).toHaveAttribute(
      "aria-invalid",
      "true",
    );
    await expect(page.getByLabel("Nowe hasło")).not.toHaveAttribute(
      "aria-invalid",
      "true",
    );
    await expect(page).toHaveURL(/\/pl\/reset-password\/confirm$/);
  });

  test("shows a password below the minimum length at the password field", async ({
    page,
  }) => {
    const { seen } = await stubAllauth(page);

    await page.goto("/pl/reset-password/confirm");
    await page.getByLabel("Kod z e-maila").fill(CODE);
    await page.getByLabel("Nowe hasło").fill("krotkie");
    await page.getByRole("button", { name: "Ustaw hasło" }).click();

    await expect(
      page.getByText("Hasło musi mieć co najmniej 8 znaków."),
    ).toBeVisible();
    await expect(page.getByLabel("Nowe hasło")).toHaveAttribute(
      "aria-invalid",
      "true",
    );
    await expect(page.getByLabel("Kod z e-maila")).not.toHaveAttribute(
      "aria-invalid",
      "true",
    );
    expect(seen.resetCalls).toBe(0);
    await expect(page).toHaveURL(/\/pl\/reset-password\/confirm$/);
  });

  test("renders both screens in the language of the prefix", async ({
    page,
  }) => {
    await stubAllauth(page);

    await page.goto("/en/reset-password");
    await expect(
      page.getByRole("heading", { name: "Recover your password" }),
    ).toBeVisible();
    await page.getByLabel("Email", { exact: true }).fill(EMAIL);
    await page.getByRole("button", { name: "Send the code" }).click();

    await expect(page).toHaveURL(/\/en\/reset-password\/confirm$/);
    await expect(
      page.getByRole("heading", { name: "Set a new password" }),
    ).toBeVisible();
    await expect(page.getByLabel("Code from the email")).toBeVisible();
  });

  test("opens the reset request from the sign-in screen", async ({ page }) => {
    await stubAllauth(page);

    await page.goto("/pl/login");
    await page.getByRole("link", { name: "Nie pamiętasz hasła?" }).click();

    await expect(page).toHaveURL(/\/pl\/reset-password$/);
    await expect(
      page.getByRole("heading", { name: "Odzyskaj hasło" }),
    ).toBeVisible();
  });

  test("asks to wait when the reset request hits the native 429 limit", async ({
    page,
  }) => {
    await stubAllauth(page, {
      requestStatus: 429,
      requestBody: { status: 429 },
    });

    await page.goto("/pl/reset-password");
    await page.getByLabel("E-mail", { exact: true }).fill(EMAIL);
    await page.getByRole("button", { name: "Wyślij kod" }).click();

    await expect(
      page.getByText("Zbyt wiele prób. Odczekaj chwilę."),
    ).toBeVisible();
    await expect(page).toHaveURL(/\/pl\/reset-password$/);
  });

  test("returns to requesting a new code when the reset stage is gone", async ({
    page,
  }) => {
    await stubAllauth(page, {
      resetStatus: 409,
      resetBody: { status: 409 },
    });

    await page.goto("/pl/reset-password/confirm");
    await page.getByLabel("Kod z e-maila").fill(CODE);
    await page.getByLabel("Nowe hasło").fill(NEW_PASSWORD);
    await page.getByRole("button", { name: "Ustaw hasło" }).click();

    await expect(page).toHaveURL(/\/pl\/reset-password$/);
    await expect(
      page.getByText(
        "Kod wygasł albo wykorzystano limit prób. Zamów nowy kod.",
      ),
    ).toBeVisible();
    await expect(page.getByLabel("Kod z e-maila")).toBeHidden();
  });
});
