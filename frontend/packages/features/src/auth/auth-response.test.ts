import { describe, expect, test } from "bun:test";

import { requireAuthStatus } from "./auth-response";

function response(status: number, data: unknown = {}) {
  return { status, data };
}

/**
 * Błędy walidacji allauth (400/409) mają trafiać do formularza z komunikatem
 * backendu, a 401 i 410 są normalnym krokiem protokołu (#350).
 */
describe("requireAuthStatus", () => {
  test("przepuszcza statusy protokołu sesji", () => {
    expect(requireAuthStatus(response(200), [200, 401], "Błąd")).toEqual(
      response(200),
    );
    expect(requireAuthStatus(response(401), [200, 401], "Błąd")).toEqual(
      response(401),
    );
  });

  test("rzuca komunikat backendu dla błędu walidacji", () => {
    expect(() =>
      requireAuthStatus(
        response(400, {
          errors: [{ message: "Ten adres email jest już zajęty." }],
        }),
        [200, 401],
        "Nie udało się utworzyć konta.",
      ),
    ).toThrow("Ten adres email jest już zajęty.");
  });

  test("rzuca czytelny fallback, gdy backend nie podał komunikatu", () => {
    expect(() =>
      requireAuthStatus(
        response(409, { status: 409 }),
        [200, 401],
        "Nie udało się utworzyć konta.",
      ),
    ).toThrow("Nie udało się utworzyć konta.");
  });
});
