import { describe, expect, test } from "bun:test";

import { AuthResponseError } from "@olivin/features/auth";

import {
  passwordResetErrorsFromFailure,
  passwordResetFailureKey,
  passwordResetValidationErrors,
} from "./password-reset-errors";

/**
 * Błędy resetu hasła trafiają do właściwych pól (#353).
 *
 * Schemat `@olivin/schemas` zwraca kody walidacji, a allauth — listę błędów
 * z parametrem pola. Ten moduł tłumaczy jedno i drugie na pole formularza oraz
 * klucz katalogu tekstów; same teksty zostają w `@olivin/i18n`.
 */
describe("passwordResetValidationErrors", () => {
  test("maps validation codes onto email, code and password fields", () => {
    const errors = passwordResetValidationErrors([
      { path: ["email"], message: "email_invalid" },
      { path: ["key"], message: "code_required" },
      { path: ["password"], message: "password_too_short" },
    ]);

    expect(errors).toEqual([
      { field: "email", key: "errors.emailInvalid" },
      { field: "key", key: "errors.codeRequired" },
      { field: "password", key: "errors.passwordTooShort" },
    ]);
  });

  test("ignores unknown paths and keeps one error per field", () => {
    const errors = passwordResetValidationErrors([
      { path: ["key"], message: "code_required" },
      { path: ["key"], message: "unknown_code" },
      { path: ["account"], message: "unknown" },
    ]);

    expect(errors).toEqual([{ field: "key", key: "errors.codeRequired" }]);
  });
});

describe("passwordResetErrorsFromFailure", () => {
  test("maps key and password errors from a rejected 400 reset", () => {
    const error = new AuthResponseError(
      {
        status: 400,
        data: {
          status: 400,
          errors: [
            { param: "key", code: "token_invalid", message: "Invalid key." },
          ],
        },
      },
      "Invalid key.",
    );

    expect(passwordResetErrorsFromFailure(error)).toEqual([
      { target: "key", code: "codeInvalid", message: "Invalid key." },
    ]);
  });

  test("returns null for non-response failures such as network errors", () => {
    expect(
      passwordResetErrorsFromFailure(new TypeError("Failed to fetch")),
    ).toBeNull();
  });
});

describe("passwordResetFailureKey", () => {
  function rejected(status: number, data: unknown) {
    return new AuthResponseError({ status, data }, "Rejected.");
  }

  test("turns the native reset request limit (429) into a wait message", () => {
    expect(passwordResetFailureKey(rejected(429, { status: 429 }))).toBe(
      "errors.tooManyAttempts",
    );
  });

  test("turns a lost reset stage (409) into an expired-code message", () => {
    expect(passwordResetFailureKey(rejected(409, { status: 409 }))).toBe(
      "errors.codeExpired",
    );
  });

  test("recognises a limit sent with an error code", () => {
    const error = rejected(400, {
      status: 400,
      errors: [{ code: "too_many_password_reset_attempts" }],
    });

    expect(passwordResetFailureKey(error)).toBe("errors.tooManyAttempts");
  });

  test("keeps an incorrect code at the code field", () => {
    const error = rejected(400, {
      status: 400,
      errors: [{ param: "key", code: "incorrect_code" }],
    });

    expect(passwordResetFailureKey(error)).toBe("errors.codeInvalid");
  });

  test("returns null for failures without a known meaning", () => {
    expect(
      passwordResetFailureKey(new TypeError("Failed to fetch")),
    ).toBeNull();
    expect(passwordResetFailureKey(rejected(500, { status: 500 }))).toBeNull();
  });
});
