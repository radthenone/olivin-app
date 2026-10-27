import {
  AuthResponseError,
  mapLoginErrors,
  type LoginError,
} from "@olivin/features/auth";

/**
 * Błędy pól z odrzuconego logowania.
 *
 * Wspólny `useLogin` rzuca `AuthResponseError` dla statusów spoza protokołu
 * sesji (np. 400 z listą pól). Zwraca `null` dla innych wyjątków (sieć),
 * które formularz pokazuje jako ogólny komunikat.
 */
export function loginErrorsFromFailure(error: unknown): LoginError[] | null {
  return error instanceof AuthResponseError
    ? mapLoginErrors(error.response.data)
    : null;
}

/**
 * Odrzucenie przez limit prób allauth (429).
 *
 * Logowanie kodem nie dostaje listy pól, więc o komunikacie decyduje sam
 * status — przy limicie użytkownik ma odczekać, a nie poprawiać kod.
 */
export function isTooManyAttempts(error: unknown): boolean {
  return error instanceof AuthResponseError && error.response.status === 429;
}
