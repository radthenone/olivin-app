import { useMutation, useQueryClient } from "@tanstack/react-query";
import { postAllauthClientV1AuthEmailVerify } from "@olivin/api/generated/auth/authentication-account/authentication-account";

import { getAuthClient } from "./auth-config";
import { requireAuthStatus } from "./auth-response";
import { getAuthSessionQueryKey } from "./session-query-key";

export type VerifyEmailInput = {
  key: string;
};

/**
 * Potwierdza email kodem/kluczem z allauth.
 *
 * Po poprawnej weryfikacji backend może ustawić zalogowaną sesję, więc routing
 * powinien dostać świeży stan z `auth/session`.
 */
export function useVerifyEmail() {
  const queryClient = useQueryClient();
  const client = getAuthClient();

  return useMutation({
    mutationFn: async (data: VerifyEmailInput) => {
      const response = await postAllauthClientV1AuthEmailVerify(client, data);

      requireAuthStatus(
        response,
        [200, 401],
        "Nie udało się potwierdzić emaila.",
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
