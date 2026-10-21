import { describe, expect, test } from "bun:test";

import { AuthResponseError, mapLoginErrors } from "@olivin/features/auth";

import { loginErrorsFromFailure } from "./login-errors";

/**
 * Błędy allauth trafiają do właściwego pola formularza (#349).
 *
 * Kody z backendu są tłumaczone na semantyczne nazwy, a nie na gotowe teksty —
 * katalog `@olivin/i18n` należy do warstwy interfejsu.
 */
describe("mapLoginErrors", () => {
  test("maps a password mismatch to the password field", () => {
    const errors = mapLoginErrors({
      status: 401,
      errors: [
        {
          param: "password",
          code: "email_password_mismatch",
          message: "The password is incorrect.",
        },
      ],
    });

    expect(errors).toEqual([
      {
        target: "password",
        code: "invalidCredentials",
        message: "The password is incorrect.",
      },
    ]);
  });

  test("maps invalid login without a parameter to a form error", () => {
    const errors = mapLoginErrors({
      status: 400,
      errors: [{ code: "invalid_login", message: "Invalid login." }],
    });

    expect(errors).toEqual([
      { target: "form", code: "invalidCredentials", message: "Invalid login." },
    ]);
  });

  test("maps rate limiting to a readable form error", () => {
    const errors = mapLoginErrors({
      status: 400,
      errors: [
        {
          code: "too_many_login_attempts",
          message: "Too many login attempts.",
        },
      ],
    });

    expect(errors).toEqual([
      {
        target: "form",
        code: "tooManyAttempts",
        message: "Too many login attempts.",
      },
    ]);
  });

  test("keeps an unknown backend error with its field and message", () => {
    const errors = mapLoginErrors({
      status: 400,
      errors: [
        {
          param: "email",
          code: "invalid_email",
          message: "Enter a valid email address.",
        },
      ],
    });

    expect(errors).toEqual([
      {
        target: "email",
        code: "backend",
        message: "Enter a valid email address.",
      },
    ]);
  });

  test("falls back to a generic form error when the body has no errors", () => {
    expect(mapLoginErrors({ status: 401, data: {} })).toEqual([
      { target: "form", code: "backend" },
    ]);
  });
});

/**
 * Wspólny `useLogin` rzuca `AuthResponseError` dla 400 (#350) — formularz
 * webowy nadal ma pokazać błędy przy polach, a nie ogólny komunikat.
 */
describe("loginErrorsFromFailure", () => {
  test("maps field errors from a rejected 400 login to form fields", () => {
    const error = new AuthResponseError(
      {
        status: 400,
        data: {
          status: 400,
          errors: [
            {
              param: "email",
              code: "invalid_email",
              message: "Enter a valid email address.",
            },
            { param: "password", code: "required", message: "Required." },
          ],
        },
      },
      "Enter a valid email address.",
    );

    expect(loginErrorsFromFailure(error)).toEqual([
      {
        target: "email",
        code: "backend",
        message: "Enter a valid email address.",
      },
      { target: "password", code: "backend", message: "Required." },
    ]);
  });

  test("returns null for non-response failures such as network errors", () => {
    expect(loginErrorsFromFailure(new TypeError("Failed to fetch"))).toBeNull();
  });
});
