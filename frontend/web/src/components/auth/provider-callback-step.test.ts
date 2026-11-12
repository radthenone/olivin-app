import { describe, expect, test } from "bun:test";

import { providerCallbackStep } from "./provider-callback-step";

/**
 * Wybór kroku na stronie powrotu od Google/Facebook (#355).
 *
 * Błąd od dostawcy wygrywa z sesją, bo przy anulowaniu sesja wygląda na
 * oczekującą. Pozostałe kroki wynikają ze statusu allauth.
 */
describe("providerCallbackStep", () => {
  test("shows the provider error before anything else", () => {
    expect(
      providerCallbackStep({
        error: "cancelled",
        isChecking: false,
        status: "provider_signup_required",
      }),
    ).toBe("error");
  });

  test("waits while the session is being checked", () => {
    expect(
      providerCallbackStep({
        error: null,
        isChecking: true,
        status: "unauthenticated",
      }),
    ).toBe("wait");
  });

  test("routes each allauth status to its step", () => {
    const step = (
      status: Parameters<typeof providerCallbackStep>[0]["status"],
    ) => providerCallbackStep({ error: null, isChecking: false, status });

    expect(step("mfa_required")).toBe("mfa");
    expect(step("email_verification_required")).toBe("verify_email");
    expect(step("authenticated")).toBe("home");
    expect(step("provider_signup_required")).toBe("signup");
    expect(step("unauthenticated")).toBe("failed");
  });
});
