import { useGetAllauthClientV1AuthProviderSignup } from "@olivin/api/generated/auth/authentication-providers/authentication-providers";

import { getAuthClient } from "./auth-config";

/**
 * Informacje o koncie dostawcy, które czeka na dokończenie rejestracji.
 *
 * Allauth oddaje tutaj e-mail i nazwę z Google/Facebook, więc formularz nie
 * musi pytać o adres ponownie. Zapytanie ma sens tylko w stanie
 * `provider_signup_required`; wołający decyduje, kiedy je włączyć.
 */
export function useProviderSignupInfo() {
  return useGetAllauthClientV1AuthProviderSignup(getAuthClient(), {
    query: { retry: false },
  });
}
