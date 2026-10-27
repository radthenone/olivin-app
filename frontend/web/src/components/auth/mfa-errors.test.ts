import { describe, expect, test } from "bun:test";

import { AuthResponseError } from "@olivin/features/auth";

import { mfaErrorsFromFailure } from "./mfa-errors";

/**
 * Odrzucony kod MFA trafia do pola kodu, a nie do ogólnego błędu (#354).
 *
 * Wspólny `useMfaAuthenticate` rzuca `AuthResponseError` dla 400 z listą
 * błędów allauth, więc formularz może pokazać właściwy komunikat.
 */
describe("mfaErrorsFromFailure", () => {
  test("maps an incorrect code from a rejected 400 to the code field", () => {
    const error = new AuthResponseError(
      {
        status: 400,
        data: {
          status: 400,
          errors: [
            {
              param: "code",
              code: "incorrect_code",
              message: "Incorrect code.",
            },
          ],
        },
      },
      "Incorrect code.",
    );

    expect(mfaErrorsFromFailure(error)).toEqual([
      {
        target: "code",
        code: "codeInvalid",
        message: "Incorrect code.",
      },
    ]);
  });

  test("returns null for non-response failures such as network errors", () => {
    expect(mfaErrorsFromFailure(new TypeError("Failed to fetch"))).toBeNull();
  });
});
