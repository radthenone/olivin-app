import { describe, expect, test } from "bun:test";

import { AuthResponseError } from "@olivin/features/auth";

import {
  registerErrorsFromFailure,
  registerValidationErrors,
  signupErrorKey,
  verifyEmailErrorKey,
  verifyEmailErrorsFromFailure,
} from "./signup-errors";

/**
 * Błędy rejestracji i weryfikacji kodu (#351).
 *
 * Schemat `@olivin/schemas` zwraca kody walidacji, a allauth listę błędów
 * z parametrami. Formularz dostaje z tego pole i klucz katalogu, więc teksty
 * zostają w `@olivin/i18n`, a nie w logice mapowania.
 */
describe("registerValidationErrors", () => {
  test("maps schema codes onto their form fields", () => {
    const errors = registerValidationErrors([
      { path: ["email"], message: "email_invalid" },
      { path: ["username"], message: "username_too_short" },
      { path: ["password"], message: "password_too_short" },
      { path: ["passwordConfirm"], message: "password_mismatch" },
      { path: ["consentTerms"], message: "consent_required" },
      { path: ["consentPrivacy"], message: "consent_required" },
    ]);

    expect(errors).toEqual([
      { field: "email", key: "errors.emailInvalid" },
      { field: "username", key: "errors.usernameInvalid" },
      { field: "password", key: "errors.passwordTooShort" },
      { field: "passwordConfirm", key: "errors.passwordMismatch" },
      { field: "consentTerms", key: "errors.consentRequired" },
      { field: "consentPrivacy", key: "errors.consentRequired" },
    ]);
  });

  test("keeps the first issue per field and ignores unknown paths", () => {
    const errors = registerValidationErrors([
      { path: ["username"], message: "username_too_long" },
      { path: ["username"], message: "username_invalid" },
      { path: ["phoneNumber"], message: "invalid" },
      { path: [], message: "invalid" },
    ]);

    expect(errors).toEqual([
      { field: "username", key: "errors.usernameInvalid" },
    ]);
  });

  test("falls back to the registration failure for an unknown code", () => {
    expect(
      registerValidationErrors([{ path: ["email"], message: "cos_nowego" }]),
    ).toEqual([{ field: "email", key: "errors.registrationFailed" }]);
  });
});

describe("signupErrorKey", () => {
  test("maps backend codes onto catalogue keys", () => {
    expect(signupErrorKey({ target: "email", code: "emailTaken" })).toBe(
      "errors.emailTaken",
    );
    expect(signupErrorKey({ target: "username", code: "usernameTaken" })).toBe(
      "errors.usernameTaken",
    );
    expect(
      signupErrorKey({ target: "consentPrivacy", code: "consentRequired" }),
    ).toBe("errors.consentRequired");
    expect(signupErrorKey({ target: "form", code: "tooManyAttempts" })).toBe(
      "errors.tooManyAttempts",
    );
  });

  test("names the field that failed validation", () => {
    expect(signupErrorKey({ target: "username", code: "invalid" })).toBe(
      "errors.usernameInvalid",
    );
    expect(signupErrorKey({ target: "password", code: "invalid" })).toBe(
      "errors.passwordInvalid",
    );
    expect(signupErrorKey({ target: "form", code: "invalid" })).toBe(
      "errors.registrationFailed",
    );
  });

  test("leaves unknown backend failures to the backend message", () => {
    expect(
      signupErrorKey({
        target: "form",
        code: "backend",
        message: "Brak dokumentu zgody.",
      }),
    ).toBeNull();
    expect(signupErrorKey({ target: "form", code: "backend" })).toBe(
      "errors.registrationFailed",
    );
  });
});

describe("verifyEmailErrorKey", () => {
  test("maps a wrong code and the rate limit", () => {
    expect(verifyEmailErrorKey({ target: "form", code: "codeInvalid" })).toBe(
      "errors.codeInvalid",
    );
    expect(
      verifyEmailErrorKey({ target: "form", code: "tooManyAttempts" }),
    ).toBe("errors.tooManyAttempts");
  });

  test("leaves unknown failures to the backend message", () => {
    expect(
      verifyEmailErrorKey({
        target: "form",
        code: "backend",
        message: "Awaria.",
      }),
    ).toBeNull();
    expect(verifyEmailErrorKey({ target: "form", code: "backend" })).toBe(
      "errors.verificationFailed",
    );
  });
});

describe("signup failures", () => {
  test("maps field errors from a rejected signup", () => {
    const error = new AuthResponseError(
      {
        status: 400,
        data: {
          status: 400,
          errors: [{ param: "username", code: "username_taken" }],
        },
      },
      "Taken",
    );

    expect(registerErrorsFromFailure(error)).toEqual([
      { target: "username", code: "usernameTaken" },
    ]);
  });

  test("returns null for network failures", () => {
    expect(
      registerErrorsFromFailure(new TypeError("Failed to fetch")),
    ).toBeNull();
  });

  test("maps errors from a rejected verification code", () => {
    const error = new AuthResponseError(
      {
        status: 400,
        data: { status: 400, errors: [{ param: "key", code: "invalid" }] },
      },
      "Invalid",
    );

    expect(verifyEmailErrorsFromFailure(error)).toEqual([
      { target: "form", code: "codeInvalid" },
    ]);
    expect(
      verifyEmailErrorsFromFailure(new TypeError("Failed to fetch")),
    ).toBeNull();
  });
});
