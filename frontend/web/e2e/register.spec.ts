import { expect, test, type Page } from "@playwright/test";

/**
 * Rejestracja ze zgodami i potwierdzenie e-maila kodem na webie (#351).
 *
 * Odpowiedzi allauth są podstawiane przez `page.route`, więc test sprawdza
 * całą drogę przeglądarka → Next → klient Orval → formularz bez Django.
 * Rejestracji nie da się sensownie powtórzyć na żywym backendzie (konto trzeba
 * potwierdzić kodem z prawdziwej wiadomości), dlatego w trybie
 * `E2E_LIVE_BACKEND=1` ten plik się pomija.
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

/** Signup przy wymaganym potwierdzeniu e-maila kończy się prośbą o kod. */
const verifyEmailRequiredBody = {
  status: 401,
  data: { flows: [{ id: "verify_email", is_pending: true }] },
  meta: { is_authenticated: false },
};

function authenticatedBody() {
  return {
    status: 200,
    data: { user: stubUser, methods: [] },
    meta: { is_authenticated: true },
  };
}

type StubbedRequest = {
  csrf?: string;
  signup?: unknown;
  verify?: unknown;
  signupCalls: number;
};

type StubbedResponse = { status: number; body: unknown };

type StubOptions = {
  signup?: StubbedResponse;
  verify?: StubbedResponse;
};

/**
 * Podstawia allauth w trybie przeglądarkowym: sesja startuje jako
 * niezalogowana, signup domyślnie prosi o kod, a weryfikacja kodu loguje.
 */
async function stubAllauth(
  page: Page,
  options: StubOptions = {},
): Promise<StubbedRequest> {
  const seen: StubbedRequest = { signupCalls: 0 };
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

  await page.route("**/_allauth/browser/v1/auth/signup", async (route) => {
    const request = route.request();

    seen.signupCalls += 1;
    seen.csrf = request.headers()["x-csrftoken"];
    seen.signup = request.postDataJSON();

    const response = options.signup ?? {
      status: 401,
      body: verifyEmailRequiredBody,
    };

    await route.fulfill({
      status: response.status,
      headers: { "content-type": "application/json" },
      body: JSON.stringify(response.body),
    });
  });

  await page.route(
    "**/_allauth/browser/v1/auth/email/verify",
    async (route) => {
      seen.verify = route.request().postDataJSON();

      const response = options.verify ?? {
        status: 200,
        body: authenticatedBody(),
      };

      if (response.status === 200) {
        authenticated = true;
      }

      await route.fulfill({
        status: response.status,
        headers: { "content-type": "application/json" },
        body: JSON.stringify(response.body),
      });
    },
  );

  // Wartości oglądamy w testach, nie w handlerze — wyjątek w route wiesza test.
  return seen;
}

async function fillRegisterForm(page: Page) {
  await page.getByLabel("E-mail", { exact: true }).fill("jan@example.com");
  await page.getByLabel("Nazwa użytkownika").fill("jan");
  await page.getByLabel("Hasło", { exact: true }).fill("tajne-haslo-123");
  await page.getByLabel("Powtórz hasło").fill("tajne-haslo-123");
}

async function acceptRequiredConsents(page: Page) {
  await page.getByLabel("Akceptuję regulamin.", { exact: true }).check();
  await page
    .getByLabel("Akceptuję politykę prywatności.", { exact: true })
    .check();
}

test.beforeEach(() => {
  test.skip(
    liveBackend,
    "Rejestracja wymaga podstawionych odpowiedzi allauth (kod z e-maila).",
  );
});

test.describe("registration with consents on the web", () => {
  test("creates an account, sends the consents and confirms the code", async ({
    page,
  }) => {
    const seen = await stubAllauth(page);

    await page.goto("/pl/register");
    await fillRegisterForm(page);
    await acceptRequiredConsents(page);
    await page.getByRole("button", { name: "Utwórz konto" }).click();

    await page.waitForURL("**/pl/register/verify");
    expect(seen.signup).toEqual({
      email: "jan@example.com",
      username: "jan",
      password: "tajne-haslo-123",
      consent_terms: true,
      consent_privacy: true,
      consent_marketing: false,
    });
    // Klient przeglądarkowy allauth wymaga tokenu CSRF z ciasteczka.
    expect(seen.csrf).toBe("csrf-test");

    await page.getByLabel("Kod z e-maila").fill("123456");
    await page.getByRole("button", { name: "Potwierdź e-mail" }).click();

    await expect(
      page.getByText("E-mail potwierdzony. Konto jest gotowe."),
    ).toBeVisible();
    // Sesja po weryfikacji jest zalogowana, więc nagłówek zna konto.
    await expect(page.getByText("Zalogowano jako Jan Jubiler")).toBeVisible();
    expect(seen.verify).toEqual({ key: "123456" });
  });

  test("keeps the marketing consent optional", async ({ page }) => {
    const seen = await stubAllauth(page);

    await page.goto("/pl/register");
    await fillRegisterForm(page);
    await acceptRequiredConsents(page);
    await page
      .getByLabel(
        "Chcę otrzymywać informacje marketingowe e-mailem (opcjonalnie).",
      )
      .check();
    await page.getByRole("button", { name: "Utwórz konto" }).click();

    await page.waitForURL("**/pl/register/verify");
    expect(seen.signup).toMatchObject({ consent_marketing: true });
  });

  test("blocks the submit until the required consents are accepted", async ({
    page,
  }) => {
    const seen = await stubAllauth(page);

    await page.goto("/pl/register");
    await fillRegisterForm(page);
    await page.getByRole("button", { name: "Utwórz konto" }).click();

    await expect(
      page.getByText("Zaakceptuj regulamin i politykę prywatności.").first(),
    ).toBeVisible();
    await expect(
      page.getByLabel("Akceptuję regulamin.", { exact: true }),
    ).toHaveAttribute("aria-invalid", "true");
    expect(seen.signupCalls).toBe(0);
    expect(page.url()).toContain("/pl/register");
  });

  test("shows a taken username at the username field", async ({ page }) => {
    await stubAllauth(page, {
      signup: {
        status: 400,
        body: {
          status: 400,
          errors: [
            {
              param: "username",
              code: "username_taken",
              message: "A user is already registered with this username.",
            },
          ],
        },
      },
    });

    await page.goto("/pl/register");
    await fillRegisterForm(page);
    await acceptRequiredConsents(page);
    await page.getByRole("button", { name: "Utwórz konto" }).click();

    await expect(
      page.getByText("Ta nazwa użytkownika jest już zajęta."),
    ).toBeVisible();
    await expect(page.getByLabel("Nazwa użytkownika")).toHaveAttribute(
      "aria-invalid",
      "true",
    );
    expect(page.url()).toContain("/pl/register");
  });
});

test.describe("email verification by code on the web", () => {
  test("shows a wrong or expired code at the form", async ({ page }) => {
    await stubAllauth(page, {
      verify: {
        status: 400,
        body: {
          status: 400,
          errors: [
            {
              param: "key",
              code: "invalid",
              message: "Incorrect code.",
            },
          ],
        },
      },
    });

    await page.goto("/pl/register/verify");
    await page.getByLabel("Kod z e-maila").fill("000000");
    await page.getByRole("button", { name: "Potwierdź e-mail" }).click();

    await expect(
      page.getByText("Kod jest nieprawidłowy lub wygasł."),
    ).toBeVisible();
    await expect(
      page.getByText("E-mail potwierdzony. Konto jest gotowe."),
    ).toBeHidden();
  });

  test("renders the form in the language of the prefix", async ({ page }) => {
    await stubAllauth(page);

    await page.goto("/en/register/verify");

    await expect(
      page.getByRole("button", { name: "Confirm email" }),
    ).toBeVisible();
    await expect(page.getByLabel("Code from the email")).toBeVisible();
  });
});
