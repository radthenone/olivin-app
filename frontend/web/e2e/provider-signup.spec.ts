import { expect, test, type Page } from "@playwright/test";

/**
 * Logowanie Google/Facebook na webie (#355).
 *
 * Testy podstawiają odpowiedzi allauth w trybie przeglądarkowym: przekierowanie
 * do dostawcy jest formularzem synchronicznym, a po powrocie strona czyta sesję
 * i pokazuje dokończenie rejestracji. Pełne logowanie u dostawcy wymaga
 * prawdziwych aplikacji OAuth, dlatego ten plik nie działa w trybie
 * `E2E_LIVE_BACKEND=1`.
 */

const liveBackend = process.env.E2E_LIVE_BACKEND === "1";

const providerEmail = "gosc@example.com";

const stubUser = {
  id: 11,
  display: "Gość Google",
  email: providerEmail,
  has_usable_password: false,
  username: "gosc-google",
};

const providerSignupPendingBody = {
  status: 401,
  data: { flows: [{ id: "provider_signup", is_pending: true }] },
  meta: { is_authenticated: false },
};

function authenticatedBody() {
  return {
    status: 200,
    data: { user: stubUser, methods: [] },
    meta: { is_authenticated: true },
  };
}

function providerInfoBody() {
  return {
    status: 200,
    data: {
      email: [{ email: providerEmail, primary: true, verified: true }],
      account: {
        uid: "google-uid-11",
        display: "Gość Google",
        provider: {
          id: "google",
          name: "Google",
          flows: ["provider_redirect"],
        },
      },
      user: {
        display: "Gość Google",
        email: providerEmail,
        has_usable_password: false,
        username: "",
      },
    },
    meta: { is_authenticated: false },
  };
}

type SeenProviderRequests = {
  csrf?: string;
  signup?: Record<string, unknown>;
  signupCalls: number;
};

/**
 * Podstawia sesję, informacje o koncie dostawcy i dokończenie rejestracji.
 *
 * Sesja startuje jako oczekująca na `provider_signup` (tak wygląda powrót od
 * Google dla nowego adresu), a po przyjęciu zgód przechodzi w zalogowaną.
 */
async function stubProviderFlow(page: Page): Promise<SeenProviderRequests> {
  const seen: SeenProviderRequests = { signupCalls: 0 };
  let authenticated = false;

  await page.route("**/_allauth/browser/v1/auth/session", async (route) => {
    await route.fulfill({
      status: authenticated ? 200 : 401,
      headers: {
        "content-type": "application/json",
        "set-cookie": "csrftoken=csrf-test; Path=/; SameSite=Lax",
      },
      body: JSON.stringify(
        authenticated ? authenticatedBody() : providerSignupPendingBody,
      ),
    });
  });

  await page.route(
    "**/_allauth/browser/v1/auth/provider/signup",
    async (route) => {
      const request = route.request();

      if (request.method() === "GET") {
        await route.fulfill({
          status: 200,
          headers: { "content-type": "application/json" },
          body: JSON.stringify(providerInfoBody()),
        });
        return;
      }

      seen.signupCalls += 1;
      seen.csrf = request.headers()["x-csrftoken"];
      seen.signup = request.postDataJSON() as Record<string, unknown>;
      authenticated = true;

      await route.fulfill({
        status: 200,
        headers: { "content-type": "application/json" },
        body: JSON.stringify(authenticatedBody()),
      });
    },
  );

  return seen;
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
    "Google/Facebook wymaga podstawionych odpowiedzi allauth i aplikacji OAuth.",
  );
});

test.describe("social provider authentication on the web", () => {
  test("shows Google and Facebook buttons on the login and registration pages", async ({
    page,
  }) => {
    await stubProviderFlow(page);

    await page.goto("/pl/login");
    await expect(
      page.getByRole("button", { name: "Kontynuuj z Google" }),
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Kontynuuj z Facebook" }),
    ).toBeVisible();

    await page.goto("/pl/register");
    await expect(
      page.getByRole("button", { name: "Kontynuuj z Google" }),
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Kontynuuj z Facebook" }),
    ).toBeVisible();
  });

  test("starts the allauth browser redirect with the callback URL", async ({
    page,
  }) => {
    await stubProviderFlow(page);

    let redirectBody = "";
    await page.route(
      "**/_allauth/browser/v1/auth/provider/redirect",
      async (route) => {
        redirectBody = route.request().postData() ?? "";
        await route.fulfill({
          status: 200,
          contentType: "text/html",
          body: "<p>Przekierowanie do dostawcy</p>",
        });
      },
    );

    await page.goto("/pl/login");
    const redirectRequest = page.waitForRequest(
      "**/_allauth/browser/v1/auth/provider/redirect",
    );
    await page.getByRole("button", { name: "Kontynuuj z Google" }).click();
    await redirectRequest;

    const params = new URLSearchParams(redirectBody);
    expect(params.get("provider")).toBe("google");
    expect(params.get("process")).toBe("login");
    expect(params.get("callback_url")).toBe(
      `${new URL(page.url()).origin}/pl/auth/provider/callback`,
    );
    expect(params.get("csrfmiddlewaretoken")).toBe("csrf-test");
  });

  test("completes the signup after returning from the provider", async ({
    page,
  }) => {
    const seen = await stubProviderFlow(page);

    await page.goto("/pl/auth/provider/callback");

    await expect(
      page.getByRole("heading", { name: "Dokończ rejestrację" }),
    ).toBeVisible();
    await expect(page.getByText(providerEmail)).toBeVisible();

    await page.getByLabel("Nazwa użytkownika").fill(stubUser.username);
    await acceptRequiredConsents(page);
    await page.getByRole("button", { name: "Załóż konto" }).click();

    await expect(page).toHaveURL(/\/pl$/);
    expect(seen.csrf).toBe("csrf-test");
    expect(seen.signup).toEqual({
      email: providerEmail,
      username: stubUser.username,
      consent_terms: true,
      consent_privacy: true,
      consent_marketing: false,
    });
  });

  test("shows a readable message when the provider cancels the login", async ({
    page,
  }) => {
    await stubProviderFlow(page);

    await page.goto("/pl/auth/provider/callback?error=access_denied");

    await expect(
      page.getByText("Logowanie zostało anulowane. Spróbuj ponownie."),
    ).toBeVisible();
    await expect(
      page.getByRole("link", { name: "Wróć do logowania" }),
    ).toHaveAttribute("href", "/pl/login");
  });
});
