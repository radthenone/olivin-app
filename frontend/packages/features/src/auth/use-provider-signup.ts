import { useMutation, useQueryClient } from "@tanstack/react-query";
import { postAllauthClientV1AuthProviderSignup } from "@olivin/api/generated/auth/authentication-providers/authentication-providers";

import { getAuthClient } from "./auth-config";
import { requireAuthStatus } from "./auth-response";
import { getAuthSessionQueryKey } from "./session-query-key";
import type { SignupConsents } from "./use-register";

export type ProviderSignupInput = {
  email: string;
} & SignupConsents;

/**
 * Dokańcza rejestrację po Google/Facebook (krok allauth `provider_signup`).
 *
 * Nowe konto z logowania zewnętrznego powstaje dopiero po zgodach, a po
 * odpowiedzi routing powinien dostać świeży stan sesji.
 */
export function useProviderSignup() {
  const queryClient = useQueryClient();
  const client = getAuthClient();

  return useMutation({
    mutationFn: async (data: ProviderSignupInput) => {
      const response = await postAllauthClientV1AuthProviderSignup(
        client,
        data,
      );

      requireAuthStatus(
        response,
        [200, 401],
        "Nie udało się dokończyć rejestracji.",
      );

      return response;
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: getAuthSessionQueryKey(),
      });
    },
  });
}
