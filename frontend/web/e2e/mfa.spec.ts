import { expect, test, type Page } from "@playwright/test";

/**
 * Drugi składnik logowania na webie (#354).
 *
 * Allauth po poprawnym haśle nie kończy logowania, tylko zwraca flow
 * `mfa_authenticate`. Test podstawia właśnie taką odpowiedź i sprawdza, że
 * przeglądarka pokazuje ekran MFA, przyjmuje poprawny kod i odrzuca zły.
 * Tryb `E2E_LIVE_BACKEND=1` pomija plik, bo wymaga konta z włączonym MFA.
 */
const liveBackend = process.env.E2E_LIVE_BACKEND === "1";

const stubUser = {
  id: 1,
  display: "Jan Jubiler",
  email: "jan@example.com",
  has_usable_password: true,
  username: "jan",
};

// ponytail: stub login nie sprawdza hasła, a pusta wartość blokuje walidację formularza
const PASSWORD = process.env.E2E_MFA_PASSWORD ?? "fixture-only-password";
const MFA_CODE = "123456";

const unauthBody = {
  status: 401,
  data: { flows: [{ id: "login" }] },
  meta: { is_authenticated: false },
};

/** Po haśle allauth czeka na drugi składnik, więc sesja nadal jest anonimowa. */
const mfaRequiredBody = {
  status: 401,
  data: {
    flows: [{ id: "login" }, { id: "mfa_authenticate", is_pending: true }],
  },
  meta: { is_authenticated: false },
};

function authenticatedBody() {
  return {
    status: 200,
    data: { user: stubUser, methods: [] },
    meta: { is_authenticated: true },
  };
}

type StubbedRequests = { mfaCode?: string };

/**
 * Podstawia sesję, logowanie hasłem i potwierdzenie MFA. Poprawny kod
 * przełącza sesję w stan zalogowany, zły kończy się błędem 400 allauth.
 * `mfaExpired` udaje wygasłe oczekujące logowanie: allauth odpowiada 401
 * bez flow `mfa_authenticate`.
 */
async function stubAllauth(
  page: Page,
  { mfaExpired = false }: { mfaExpired?: boolean } = {},
): Promise<StubbedRequests> {
  const seen: StubbedRequests = {};
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
    await route.fulfill({
      status: 401,
      headers: { "content-type": "application/json" },
      body: JSON.stringify(mfaRequiredBody),
    });
  });

  await page.route(
    "**/_allauth/browser/v1/auth/2fa/authenticate",
    async (route) => {
      const body = route.request().postDataJSON() as { code?: string };
      seen.mfaCode = body.code;

      if (mfaExpired) {
        await route.fulfill({
          status: 401,
          headers: { "content-type": "application/json" },
          body: JSON.stringify(unauthBody),
        });
        return;
      }

      const valid = body.code === MFA_CODE;
      authenticated = valid;

      await route.fulfill({
        status: valid ? 200 : 400,
        headers: { "content-type": "application/json" },
        body: JSON.stringify(
          valid
            ? authenticatedBody()
            : {
                status: 400,
                errors: [
                  {
                    param: "code",
                    code: "incorrect_code",
                    message: "Incorrect code.",
                  },
                ],
              },
        ),
      });
    },
  );

  return seen;
}

async function fillPasswordStep(page: Page) {
  await page.getByLabel("E-mail").fill(stubUser.email);
  await page.getByLabel("Hasło").fill(PASSWORD);
  await page.getByRole("button", { name: "Zaloguj" }).click();
}

test.beforeEach(() => {
  test.skip(
    liveBackend,
    "E2E_LIVE_BACKEND=1 wymaga konta z włączonym MFA — ten plik działa na podstawionych odpowiedziach.",
  );
});

test.describe("MFA step after password on the web", () => {
  test("asks for the second factor and signs in with a valid code", async ({
    page,
  }) => {
    const seen = await stubAllauth(page);

    await page.goto("/pl/login");
    await fillPasswordStep(page);

    await expect(
      page.getByRole("heading", { name: "Weryfikacja dwuetapowa" }),
    ).toBeVisible();
    await expect(page.getByRole("link", { name: "Zaloguj się" })).toBeVisible();

    await page.getByLabel("Kod MFA").fill(MFA_CODE);
    await page.getByRole("button", { name: "Potwierdź" }).click();

    await expect(page.getByText(stubUser.display)).toBeVisible();
    await expect(page.getByRole("button", { name: "Wyloguj" })).toBeVisible();
    expect(seen.mfaCode).toBe(MFA_CODE);
  });

  test("shows an error for a wrong code and keeps the user signed out", async ({
    page,
  }) => {
    await stubAllauth(page);

    await page.goto("/pl/login");
    await fillPasswordStep(page);

    await page.getByLabel("Kod MFA").fill("000000");
    await page.getByRole("button", { name: "Potwierdź" }).click();

    await expect(page.getByText("Nieprawidłowy kod MFA.")).toBeVisible();
    await expect(page.getByRole("link", { name: "Zaloguj się" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Wyloguj" })).toBeHidden();
  });

  test("returns to the password step when the pending login expired", async ({
    page,
  }) => {
    await stubAllauth(page, { mfaExpired: true });

    await page.goto("/pl/login");
    await fillPasswordStep(page);

    await page.getByLabel("Kod MFA").fill(MFA_CODE);
    await page.getByRole("button", { name: "Potwierdź" }).click();

    await expect(
      page.getByText("Logowanie wygasło. Zaloguj się ponownie."),
    ).toBeVisible();
    await expect(page.getByLabel("Hasło")).toBeVisible();
    await expect(page.getByLabel("Kod MFA")).toBeHidden();
  });
});
