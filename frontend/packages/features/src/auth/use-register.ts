import { useMutation, useQueryClient } from "@tanstack/react-query";
import { postAllauthClientV1AuthSignup } from "@olivin/api/generated/auth/authentication-account/authentication-account";

import { getAuthClient } from "./auth-config";
import { requireAuthStatus } from "./auth-response";
import { getAuthSessionQueryKey } from "./session-query-key";

export type SignupConsents = {
  consent_terms: boolean;
  consent_privacy: boolean;
  consent_marketing?: boolean;
};

export type RegisterInput = {
  email: string;
  password: string;
  firstName: string;
  lastName: string;
  dateOfBirth: string;
  phoneNumber: string;
} & SignupConsents;

/**
 * Rejestruje użytkownika przez allauth.
 *
 * Signup może od razu zwrócić stan wymagający weryfikacji email albo zalogowaną
 * sesję, więc po odpowiedzi odświeżamy wygenerowany klucz sesji.
 */
export function useRegister() {
  const queryClient = useQueryClient();
  const client = getAuthClient();

  return useMutation({
    mutationFn: async (data: RegisterInput) => {
      const response = await postAllauthClientV1AuthSignup(client, data);

      requireAuthStatus(response, [200, 401], "Nie udało się utworzyć konta.");

      return response;
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: getAuthSessionQueryKey(),
      });
    },
  });
}
