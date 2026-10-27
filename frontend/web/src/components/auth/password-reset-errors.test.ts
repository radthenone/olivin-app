import { describe, expect, test } from "bun:test";

import { AuthResponseError } from "@olivin/features/auth";

import {
  isTooManyAttempts,
  passwordResetErrorsFromFailure,
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

describe("isTooManyAttempts", () => {
  test("recognises the allauth rate limit by status", () => {
    const error = new AuthResponseError({ status: 429, data: {} }, "Too many");

    expect(isTooManyAttempts(error)).toBe(true);
  });

  test("ignores other failures", () => {
    expect(isTooManyAttempts(new TypeError("Failed to fetch"))).toBe(false);
  });
});
