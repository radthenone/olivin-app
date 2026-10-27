import { describe, expect, test } from "bun:test";

import { providerErrorKey } from "./provider-error-key";

/**
 * Komunikaty po powrocie od Google/Facebook (#355).
 *
 * Allauth dokłada do `callback_url` parametr `error`; interfejs zamienia go na
 * klucz katalogu, żeby anulowanie przez użytkownika nie wyglądało jak awaria.
 */
describe("providerErrorKey", () => {
  test("treats the provider's access denial as a cancellation", () => {
    expect(providerErrorKey("access_denied")).toBe(
      "auth.provider.errors.cancelled",
    );
    expect(providerErrorKey("cancelled")).toBe(
      "auth.provider.errors.cancelled",
    );
  });

  test("explains when the provider or signup policy refused the account", () => {
    expect(providerErrorKey("denied")).toBe(
      "auth.provider.errors.notAllowed",
    );
    expect(providerErrorKey("permission_denied")).toBe(
      "auth.provider.errors.notAllowed",
    );
    expect(providerErrorKey("signup_closed")).toBe(
      "auth.provider.errors.notAllowed",
    );
  });

  test("asks for a fresh sign-in when reauthentication is required", () => {
    expect(providerErrorKey("reauthentication_required")).toBe(
      "auth.provider.errors.reauthentication",
    );
  });

  test("falls back to a generic provider failure", () => {
    expect(providerErrorKey("unknown")).toBe("auth.provider.errors.failed");
    expect(providerErrorKey(undefined)).toBe("auth.provider.errors.failed");
    expect(providerErrorKey(null)).toBe("auth.provider.errors.failed");
  });
});
