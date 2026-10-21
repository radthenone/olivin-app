import { expect, test, type Page } from "@playwright/test";

/**
 * Rejestracja e-mailem ze zgodami i potwierdzenie e-maila kodem (#351).
 *
 * Odpowiedzi allauth są podstawiane przez `page.route`, więc test sprawdza
 * cały łańcuch przeglądarka → Next → klient Orval → formularz bez Django.
 */

const stubUser = {
  id: 7,
  display: "nowy@example.com",
  email: "nowy@example.com",
  has_usable_password: true,
  username: "nowy",
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

function pendingVerificationBody() {
  return {
    status: 401,
    data: { flows: [{ id: "verify_email", is_pending: true }] },
    meta: { is_authenticated: false },
  };
}

type SeenRequests = {
  csrf?: string;
  signup?: Record<string, unknown>;
  verify?: Record<string, unknown>;
};

type StubOptions = {
  signupStatus?: number;
  signupBody?: unknown;
  verifyStatus?: number;
  verifyBody?: unknown;
};

/**
 * Podstawia sesję, rejestrację i weryfikację kodu allauth w trybie
 * przeglądarkowym. Sesja zawsze jest niezalogowana — formularz weryfikacji
 * pokazuje sukces na podstawie odpowiedzi `email/verify`.
 */
async function stubAllauth(
  page: Page,
  options: StubOptions = {},
): Promise<SeenRequests> {
  const seen: SeenRequests = {};

  await page.route("**/_allauth/browser/v1/auth/session", async (route) => {
    await route.fulfill({
      status: 401,
      headers: {
        "content-type": "application/json",
        "set-cookie": "csrftoken=csrf-test; Path=/; SameSite=Lax",
      },
      body: JSON.stringify(unauthBody),
    });
  });

  await page.route("**/_allauth/browser/v1/auth/signup", async (route) => {
    const request = route.request();

    seen.csrf = request.headers()["x-csrftoken"];
    seen.signup = request.postDataJSON() as Record<string, unknown>;

    await route.fulfill({
      status: options.signupStatus ?? 401,
      headers: { "content-type": "application/json" },
      body: JSON.stringify(options.signupBody ?? pendingVerificationBody()),
    });
  });

  await page.route(
    "**/_allauth/browser/v1/auth/email/verify",
    async (route) => {
      seen.verify = route.request().postDataJSON() as Record<string, unknown>;

      await route.fulfill({
        status: options.verifyStatus ?? 200,
        headers: { "content-type": "application/json" },
        body: JSON.stringify(options.verifyBody ?? authenticatedBody()),
      });
    },
  );

  return seen;
}

async function fillRegistrationForm(
  page: Page,
  values = {
    email: "nowy@example.com",
    username: "nowy",
    password: "tajne-haslo",
  },
) {
  await page.getByLabel("E-mail", { exact: true }).fill(values.email);
  await page.getByLabel("Nazwa użytkownika").fill(values.username);
  await page.getByLabel("Hasło", { exact: true }).fill(values.password);
  await page.getByLabel("Powtórz hasło").fill(values.password);
}

test.describe("registration on the web", () => {
  test("creates an account with the required consents and moves to email verification", async ({
    page,
  }) => {
    const seen = await stubAllauth(page);

    await page.goto("/pl/register");
    await fillRegistrationForm(page);

    await page.getByLabel("Akceptuję regulamin.").check();
    await page.getByLabel("Akceptuję politykę prywatności.").check();

    await page.getByRole("button", { name: "Utwórz konto" }).click();

    await expect(page).toHaveURL(/\/pl\/register\/verify$/);

    expect(seen.csrf).toBe("csrf-test");
    expect(seen.signup).toMatchObject({
      email: "nowy@example.com",
      username: "nowy",
      password: "tajne-haslo",
      consent_terms: true,
      consent_privacy: true,
      consent_marketing: false,
    });
  });

  test("blocks submission until both required consents are accepted", async ({
    page,
  }) => {
    const seen = await stubAllauth(page);

    await page.goto("/pl/register");
    await fillRegistrationForm(page);

    await page.getByRole("button", { name: "Utwórz konto" }).click();

    await expect(
      page.getByText("Zaakceptuj regulamin i politykę prywatności.").first(),
    ).toBeVisible();
    await expect(page).toHaveURL(/\/pl\/register$/);
    expect(seen.signup).toBeUndefined();
  });

  test("shows a taken username at the username field", async ({ page }) => {
    await stubAllauth(page, {
      signupStatus: 400,
      signupBody: {
        status: 400,
        meta: { is_authenticated: false },
        errors: [
          {
            param: "username",
            code: "username_taken",
            message: "A user is already registered with this username.",
          },
        ],
      },
    });

    await page.goto("/pl/register");
    await fillRegistrationForm(page);
    await page.getByLabel("Akceptuję regulamin.").check();
    await page.getByLabel("Akceptuję politykę prywatności.").check();

    await page.getByRole("button", { name: "Utwórz konto" }).click();

    await expect(
      page.getByText("Ta nazwa użytkownika jest już zajęta."),
    ).toBeVisible();
    await expect(page.getByLabel("Nazwa użytkownika")).toHaveAttribute(
      "aria-invalid",
      "true",
    );
    await expect(page).toHaveURL(/\/pl\/register$/);
  });

  test("confirms the email with the code from the message", async ({
    page,
  }) => {
    const seen = await stubAllauth(page);

    await page.goto("/pl/register/verify");
    await page.getByLabel("Kod z e-maila").fill("123456");
    await page.getByRole("button", { name: "Potwierdź e-mail" }).click();

    await expect(
      page.getByText("E-mail potwierdzony. Konto jest gotowe."),
    ).toBeVisible();
    expect(seen.verify).toEqual({ key: "123456" });
  });

  test("shows a wrong or expired code on the verification form", async ({
    page,
  }) => {
    await stubAllauth(page, {
      verifyStatus: 400,
      verifyBody: {
        status: 400,
        meta: { is_authenticated: false },
        errors: [
          {
            param: "key",
            code: "invalid",
            message: "Invalid or expired key.",
          },
        ],
      },
    });

    await page.goto("/pl/register/verify");
    await page.getByLabel("Kod z e-maila").fill("000000");
    await page.getByRole("button", { name: "Potwierdź e-mail" }).click();

    await expect(
      page.getByText("Kod jest nieprawidłowy lub wygasł."),
    ).toBeVisible();
  });
});
