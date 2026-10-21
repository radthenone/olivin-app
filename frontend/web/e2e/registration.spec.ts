import { expect, test, type Page } from "@playwright/test";

/**
 * Rejestracja e-mailem ze zgodami i potwierdzenie e-maila kodem (#351).
 *
 * Odpowiedzi allauth są podstawiane przez `page.route`, więc test sprawdza
 * cały łańcuch przeglądarka → Next → klient Orval → formularz bez Django.
 * Rejestracji nie da się sensownie powtórzyć na żywym backendzie (założone
 * konto trzeba potwierdzić kodem z prawdziwej wiadomości), dlatego w trybie
 * `E2E_LIVE_BACKEND=1` ten plik się pomija.
 */

const liveBackend = process.env.E2E_LIVE_BACKEND === "1";

const stubUser = {
  id: 7,
  display: "nowy@example.com",
  email: "nowy@example.com",
  has_usable_password: true,
  username: "nowy",
};

const PASSWORD = "tajne-haslo-123";

const unauthBody = {
  status: 401,
  data: { flows: [{ id: "login" }] },
  meta: { is_authenticated: false },
};

/** Signup przy wymaganym potwierdzeniu e-maila kończy się prośbą o kod. */
function pendingVerificationBody() {
  return {
    status: 401,
    data: { flows: [{ id: "verify_email", is_pending: true }] },
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
  signup?: Record<string, unknown>;
  verify?: Record<string, unknown>;
  signupCalls: number;
};

type StubOptions = {
  signupStatus?: number;
  signupBody?: unknown;
  verifyStatus?: number;
  verifyBody?: unknown;
};

type Stub = {
  seen: SeenRequests;
};

/**
 * Podstawia sesję, rejestrację i weryfikację kodu allauth w trybie
 * przeglądarkowym. Sesja startuje jako niezalogowana i loguje się dopiero po
 * przyjęciu kodu — tak zachowuje się allauth po potwierdzeniu e-maila.
 */
async function stubAllauth(
  page: Page,
  options: StubOptions = {},
): Promise<Stub> {
  const seen: SeenRequests = { signupCalls: 0 };
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

      const status = options.verifyStatus ?? 200;
      if (status === 200) {
        authenticated = true;
      }

      await route.fulfill({
        status,
        headers: { "content-type": "application/json" },
        body: JSON.stringify(options.verifyBody ?? authenticatedBody()),
      });
    },
  );

  // Wartości oglądamy w testach, nie w handlerze — wyjątek w route wiesza test.
  return { seen };
}

async function fillRegistrationForm(page: Page) {
  await page.getByLabel("E-mail", { exact: true }).fill(stubUser.email);
  await page.getByLabel("Nazwa użytkownika").fill(stubUser.username);
  await page.getByLabel("Hasło", { exact: true }).fill(PASSWORD);
  await page.getByLabel("Powtórz hasło").fill(PASSWORD);
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

test.describe("registration on the web", () => {
  test("creates an account with the required consents and moves to email verification", async ({
    page,
  }) => {
    const { seen } = await stubAllauth(page);

    await page.goto("/pl/register");
    await fillRegistrationForm(page);
    await acceptRequiredConsents(page);
    await page.getByRole("button", { name: "Utwórz konto" }).click();

    await expect(page).toHaveURL(/\/pl\/register\/verify$/);

    expect(seen.csrf).toBe("csrf-test");
    expect(seen.signup).toEqual({
      email: stubUser.email,
      username: stubUser.username,
      password: PASSWORD,
      consent_terms: true,
      consent_privacy: true,
      consent_marketing: false,
    });
  });

  test("keeps the marketing consent optional", async ({ page }) => {
    const { seen } = await stubAllauth(page);

    await page.goto("/pl/register");
    await fillRegistrationForm(page);
    await acceptRequiredConsents(page);
    await page
      .getByLabel(
        "Chcę otrzymywać informacje marketingowe e-mailem (opcjonalnie).",
      )
      .check();
    await page.getByRole("button", { name: "Utwórz konto" }).click();

    await expect(page).toHaveURL(/\/pl\/register\/verify$/);
    expect(seen.signup).toMatchObject({ consent_marketing: true });
  });

  test("blocks submission until both required consents are accepted", async ({
    page,
  }) => {
    const { seen } = await stubAllauth(page);

    await page.goto("/pl/register");
    await fillRegistrationForm(page);
    await page.getByRole("button", { name: "Utwórz konto" }).click();

    await expect(
      page.getByText("Zaakceptuj regulamin i politykę prywatności.").first(),
    ).toBeVisible();
    await expect(
      page.getByLabel("Akceptuję regulamin.", { exact: true }),
    ).toHaveAttribute("aria-invalid", "true");
    await expect(page).toHaveURL(/\/pl\/register$/);
    expect(seen.signupCalls).toBe(0);
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
    await acceptRequiredConsents(page);
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
});

test.describe("email verification by code on the web", () => {
  test("confirms the email with the code from the message", async ({
    page,
  }) => {
    const { seen } = await stubAllauth(page);

    await page.goto("/pl/register/verify");
    await page.getByLabel("Kod z e-maila").fill("123456");
    await page.getByRole("button", { name: "Potwierdź e-mail" }).click();

    await expect(
      page.getByText("E-mail potwierdzony. Konto jest gotowe."),
    ).toBeVisible();
    // Potwierdzony e-mail oznacza zalogowaną sesję, więc nagłówek zna konto.
    await expect(
      page.getByText(`Zalogowano jako ${stubUser.display}`),
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
