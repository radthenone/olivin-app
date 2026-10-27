import {
  AuthResponseError,
  mapMfaErrors,
  type MfaError,
} from "@olivin/features/auth";

/**
 * Błędy pola kodu z odrzuconego potwierdzenia MFA.
 *
 * Wspólny `useMfaAuthenticate` rzuca `AuthResponseError` dla 400 z listą
 * błędów allauth. Zwraca `null` dla innych wyjątków (sieć), które formularz
 * pokazuje jako ogólny komunikat.
 */
export function mfaErrorsFromFailure(error: unknown): MfaError[] | null {
  return error instanceof AuthResponseError
    ? mapMfaErrors(error.response.data)
    : null;
}
